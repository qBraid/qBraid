# Copyright (C) 2020 Unitary Fund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module containing functions to convert between Cirq's circuit
representation and Qiskit's circuit representation.

"""
import copy
from typing import Any, List, Optional, Tuple

import cirq
import numpy as np
import qiskit

from qbraid.interface import convert_to_contiguous
from qbraid.interface.qbraid_cirq.tools import _convert_to_line_qubits
from qbraid.transpiler.cirq_utils import from_qasm, to_qasm
from qbraid.transpiler.cirq_utils.custom_gates import _map_zpow_and_unroll

QASMType = str


def _map_bit_index(bit_index: int, new_register_sizes: List[int]) -> Tuple[int, int]:
    """Returns the register index and (qu)bit index in this register for the
    mapped bit_index.

    Args:
        bit_index: Index of (qu)bit in the original register.
        new_register_sizes: List of sizes of the new registers.

    Example:
        bit_index = 3, new_register_sizes = [2, 3]
        returns (1, 0), meaning the mapped (qu)bit is in the 1st new register
        and has index 0 in this register.

    Note:
        The bit_index is assumed to come from a circuit with 1 or n registers
        where n is the maximum bit_index.
    """
    max_indices_in_registers = np.cumsum(new_register_sizes) - 1

    # Could be faster via bisection.
    register_index = None
    for count, bit_index_iter in enumerate(max_indices_in_registers):
        if bit_index <= bit_index_iter:
            register_index = count
            break
    assert register_index is not None

    if register_index == 0:
        return register_index, bit_index

    return (
        register_index,
        bit_index - max_indices_in_registers[register_index - 1] - 1,
    )


def _map_qubits(
    qubits: List[qiskit.circuit.Qubit],
    new_register_sizes: List[int],
    new_registers: List[qiskit.QuantumRegister],
) -> List[qiskit.circuit.Qubit]:
    """Maps qubits to new registers.

    Args:
        qubits: A list of qubits to map.
        new_register_sizes: The size(s) of the new registers to map to.
            Note: These can be determined from ``new_registers``, but this
            helper function is only called from ``_map_qubits`` where the sizes
            are already computed.
        new_registers: The new registers to map the ``qubits`` to.

    Returns:
        The input ``qubits`` mapped to the ``new_registers``.
    """
    indices = [bit.index for bit in qubits]
    mapped_indices = [_map_bit_index(i, new_register_sizes) for i in indices]
    return [qiskit.circuit.Qubit(new_registers[i], j) for i, j in mapped_indices]


def _measurement_order(
    circuit: qiskit.QuantumCircuit,
) -> List[Tuple[Any, ...]]:
    """Returns the left-to-right measurement order in the circuit.

    The "measurement order" is a list of tuples (qubit, bit) involved in
    measurements ordered as they appear going left-to-right through the circuit
    (i.e., iterating through circuit.data). The purpose of this is to be able
    to do

    >>> for (qubit, bit) in _measurement_order(circuit):
    >>>     other_circuit.measure(qubit, bit)

    which ensures ``other_circuit`` has the same measurement order as
    ``circuit``, assuming ``other_circuit`` has the same register(s) as
    ``circuit``.

    Args:
        circuit: Qiskit circuit to get the measurement order of.
    """
    order = []
    for (gate, qubits, cbits) in circuit.data:
        if isinstance(gate, qiskit.circuit.Measure):
            if len(qubits) != 1 or len(cbits) != 1:
                raise ValueError(
                    f"Only measurements with one qubit and one bit are "
                    f"supported, but this measurement has {len(qubits)} "
                    f"qubit(s) and {len(cbits)} bit(s)."
                )
            order.append((*qubits, *cbits))
    return order


def _transform_registers(
    circuit: qiskit.QuantumCircuit,
    new_qregs: Optional[List[qiskit.QuantumRegister]] = None,
) -> None:
    """Transforms the registers in the circuit to the new registers.

    Args:
        circuit: Qiskit circuit with at most one quantum register.
        new_qregs: The new quantum registers for the circuit.

    Raises:
        ValueError:
            * If the input circuit has more than one quantum register.
            * If the number of qubits in the new quantum registers does not
            match the number of qubits in the circuit.
    """
    if new_qregs is None:
        return

    if len(circuit.qregs) > 1:
        raise ValueError(
            "Input circuit is required to have <= 1 quantum register but has "
            f"{len(circuit.qregs)} quantum registers."
        )

    qreg_sizes = [qreg.size for qreg in new_qregs]
    nqubits_in_circuit = sum(qreg.size for qreg in circuit.qregs)

    if len(qreg_sizes) and sum(qreg_sizes) < nqubits_in_circuit:
        raise ValueError(
            f"The circuit has {nqubits_in_circuit} qubit(s), but the provided "
            f"quantum registers have {sum(qreg_sizes)} qubit(s)."
        )

    # Copy the circuit data.
    data = copy.deepcopy(circuit._data)

    # Remove the old qubits and add the new ones.
    circuit._qubits = []
    circuit._qubit_set = set()
    circuit.qregs = []
    circuit._data = []
    circuit.add_register(*new_qregs)

    # Map the qubits in operations to the new qubits.
    new_ops = []
    for op in data:
        gate, qubits, cbits = op
        new_qubits = _map_qubits(qubits, qreg_sizes, new_qregs)
        new_ops.append((gate, new_qubits, cbits))

    circuit._data = new_ops


def _map_qasm_str_to_def(qasm_str):
    gate_defs = {}
    qasm_lst = qasm_str.split("\n")
    qasm_lst_out = []
    for _, qasm_line in enumerate(qasm_lst):
        line_str = qasm_line
        line_args = line_str.split(" ")
        if line_args[0] == "gate":
            gate = line_args[1]
            qs = line_args[2].split(",")
            instr = line_str.split("{")[1].strip("}").strip()
            gate_defs[gate] = (qs, instr)
            line_str_out = "// " + line_str
        elif line_args[0] in gate_defs:
            qs, instr = gate_defs[line_args[0]]
            map_qs = line_args[1].strip(";").split(",")
            for i, qs_i in enumerate(qs):
                instr = instr.replace(qs_i, map_qs[i])
            line_str_out = instr
        else:
            line_str_out = line_str
        qasm_lst_out.append(line_str_out)
    return "\n".join(qasm_lst_out)


def to_qiskit(circuit: cirq.Circuit) -> qiskit.QuantumCircuit:
    """Returns a Qiskit circuit equivalent to the input Cirq circuit. Note
    that the output circuit registers may not match the input circuit
    registers.

    Args:
        circuit: Cirq circuit to convert to a Qiskit circuit.

    Returns:
        Qiskit.QuantumCircuit object equivalent to the input Cirq circuit.
    """
    contig_circuit = convert_to_contiguous(circuit, rev_qubits=True)
    compat_circuit = _map_zpow_and_unroll(contig_circuit)
    return qiskit.QuantumCircuit.from_qasm_str(to_qasm(compat_circuit))


def from_qiskit(circuit: qiskit.QuantumCircuit) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input Qiskit circuit.

    Args:
        circuit: Qiskit circuit to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input Qiskit circuit.
    """
    qasm_str = circuit.qasm()
    qasm_str_def = _map_qasm_str_to_def(qasm_str)
    cirq_circuit = from_qasm(qasm_str_def)
    return _convert_to_line_qubits(cirq_circuit, rev_qubits=True)

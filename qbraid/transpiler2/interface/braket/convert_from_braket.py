# Copyright (C) 2021 Unitary Fund
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
from multiprocessing.sharedctypes import Value
from typing import Any, Dict, List

import numpy as np

from cirq import (
    Circuit,
    LineQubit,
    ops as cirq_ops,
    protocols,
)
from braket.circuits import (
    gates as braket_gates,
    Circuit as BKCircuit,
    Instruction as BKInstruction,
)
from braket.circuits.unitary_calculation import calculate_unitary

from qbraid.transpiler2.utils import _create_unitary_gate_cirq


def _gate_to_matrix_braket(gate: braket_gates.Unitary) -> np.ndarray:
    matrix = gate.to_matrix()
    unitary_gate = braket_gates.Unitary(matrix)
    nqubits = int(np.log2(len(matrix)))
    qubits = [i for i in range(nqubits)] if nqubits > 1 else 0
    circuit = BKCircuit([BKInstruction(unitary_gate, qubits)])
    return calculate_unitary(circuit.qubit_count, circuit.instructions)


def _contiguous_compression_braket(circuit: BKCircuit, rev_qubits=False) -> BKCircuit:
    """Checks whether the circuit uses contiguous qubits/indices,
    and if not, reduces dimension accordingly."""
    qubit_map = {}
    circuit_qubits = list(circuit.qubits)
    circuit_qubits.sort()
    if rev_qubits:
        circuit_qubits = list(reversed(circuit_qubits))
    for index, qubit in enumerate(circuit_qubits):
        qubit_map[int(qubit)] = index
    contig_circuit = BKCircuit()
    for instr in circuit.instructions:
        contig_qubits = [qubit_map[int(qubit)] for qubit in list(instr.target)]
        contig_instr = BKInstruction(instr.operator, target=contig_qubits)
        contig_circuit.add_instruction(contig_instr)
    return contig_circuit


def from_braket(circuit: BKCircuit) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Braket circuit.

    Note: The returned Cirq circuit acts on cirq.LineQubit's with indices equal
    to the qubit indices of the Braket circuit.

    Args:
        circuit: Braket circuit to convert to a Cirq circuit.
    """
    compat_circuit = _contiguous_compression_braket(circuit, rev_qubits=True)
    BK_qubits = [int(q) for q in compat_circuit.qubits]
    cirq_qubits = [LineQubit(x) for x in range(len(BK_qubits))]
    qubit_mapping = {x: cirq_qubits[x] for x in range(len(cirq_qubits))}
    return Circuit(
        _translate_braket_instruction_to_cirq_operation(instr, qubit_mapping)
        for instr in compat_circuit.instructions
    )


def _translate_braket_instruction_to_cirq_operation(
    instr: BKInstruction, qubit_mapping: Dict[int, LineQubit]
) -> List[cirq_ops.Operation]:
    """Converts the braket instruction to an equivalent Cirq operation or list
    of Cirq operations.

    Args:
        instr: Braket instruction to convert.
        qubit_mapping: Braket qubit indicies mapped to indexed Cirq LineQubits

    Raises:
        ValueError: If the instruction cannot be converted to Cirq.
    """
    nqubits = len(instr.target)
    BK_qubits = [int(q) for q in instr.target]
    qubits = [qubit_mapping[x] for x in BK_qubits]

    if nqubits == 1:
        return _translate_one_qubit_braket_instruction_to_cirq_operation(instr, qubits)

    elif nqubits == 2:
        return _translate_two_qubit_braket_instruction_to_cirq_operation(instr, qubits)

    elif nqubits == 3:
        if isinstance(instr.operator, braket_gates.CCNot):
            return [cirq_ops.TOFFOLI.on(*qubits)]
        elif isinstance(instr.operator, braket_gates.CSwap):
            return [cirq_ops.FREDKIN.on(*qubits)]
        else:
            try:
                matrix = _gate_to_matrix_braket(instr.operator)
                return [cirq_ops.MatrixGate(matrix).on(*qubits)]
            except (ValueError, TypeError) as err:
                raise ValueError(f"Unable to convert the instruction {instr} to Cirq.") from err

    # Unknown instructions.
    else:
        raise ValueError(
            f"Unable to convert to Cirq due to unrecognized \
            instruction: {instr}."
        )

    return None  # type: ignore[return-value]  # pragma: no cover


def _translate_one_qubit_braket_instruction_to_cirq_operation(
    instr: BKInstruction, qubits: List[LineQubit]
) -> List[cirq_ops.Operation]:
    """Converts the one-qubit braket instruction to Cirq.

    Args:
        instr: One-qubit Braket instruction to convert.
        qubits: Cirq LineQubit list indexed according to Braket instruction

    Raises:
        ValueError: If the instruction cannot be converted to Cirq.
    """
    gate = instr.operator

    # One-qubit non-parameterized gates.
    if isinstance(gate, braket_gates.I):
        return [cirq_ops.I.on(*qubits)]
    elif isinstance(gate, braket_gates.X):
        return [cirq_ops.X.on(*qubits)]
    elif isinstance(gate, braket_gates.Y):
        return [cirq_ops.Y.on(*qubits)]
    elif isinstance(gate, braket_gates.Z):
        return [cirq_ops.Z.on(*qubits)]
    elif isinstance(gate, braket_gates.H):
        return [cirq_ops.H.on(*qubits)]
    elif isinstance(gate, braket_gates.S):
        return [cirq_ops.S.on(*qubits)]
    elif isinstance(gate, braket_gates.Si):
        return [protocols.inverse(cirq_ops.S.on(*qubits))]
    elif isinstance(gate, braket_gates.T):
        return [cirq_ops.T.on(*qubits)]
    elif isinstance(gate, braket_gates.Ti):
        return [protocols.inverse(cirq_ops.T.on(*qubits))]
    elif isinstance(gate, braket_gates.V):
        return [cirq_ops.X.on(*qubits) ** 0.5]
    elif isinstance(gate, braket_gates.Vi):
        return [cirq_ops.X.on(*qubits) ** -0.5]

    # One-qubit parameterized gates.
    elif isinstance(gate, braket_gates.Rx):
        return [cirq_ops.rx(gate.angle).on(*qubits)]
    elif isinstance(gate, braket_gates.Ry):
        return [cirq_ops.ry(gate.angle).on(*qubits)]
    elif isinstance(gate, braket_gates.Rz):
        return [cirq_ops.rz(gate.angle).on(*qubits)]
    elif isinstance(gate, braket_gates.PhaseShift):
        return [cirq_ops.Z.on(*qubits) ** (gate.angle / np.pi)]

    else:
        try:
            matrix = _gate_to_matrix_braket(gate)
            return [cirq_ops.MatrixGate(matrix).on(*qubits)]
        except (ValueError, TypeError) as err:
            raise ValueError(f"Unable to convert the instruction {instr} to Cirq.") from err

    return None  # type: ignore[return-value]  # pragma: no cover


def _translate_two_qubit_braket_instruction_to_cirq_operation(
    instr: BKInstruction, qubits: List[LineQubit]
) -> List[cirq_ops.Operation]:
    """Converts the two-qubit braket instruction to Cirq.

    Args:
        instr: Two-qubit Braket instruction to convert.
        qubits: Cirq LineQubit list indexed according to Braket instruction

    Raises:
        ValueError: If the instruction cannot be converted to Cirq.
    """
    gate = instr.operator

    # Two-qubit non-parameterized gates.
    if isinstance(gate, braket_gates.CNot):
        return [cirq_ops.CNOT.on(*qubits)]

    elif isinstance(gate, braket_gates.Swap):
        return [cirq_ops.SWAP.on(*qubits)]
    elif isinstance(gate, braket_gates.ISwap):
        return [cirq_ops.ISWAP.on(*qubits)]
    elif isinstance(gate, braket_gates.CZ):
        return [cirq_ops.CZ.on(*qubits)]
    elif isinstance(gate, braket_gates.CY):
        return [
            protocols.inverse(cirq_ops.S.on(qubits[1])),
            cirq_ops.CNOT.on(*qubits),
            cirq_ops.S.on(qubits[1]),
        ]

    # Two-qubit parameterized gates.
    elif isinstance(gate, braket_gates.CPhaseShift):
        return [cirq_ops.CZ.on(*qubits) ** (gate.angle / np.pi)]
    elif isinstance(gate, braket_gates.CPhaseShift00):
        return [
            cirq_ops.XX(*qubits),
            cirq_ops.CZ.on(*qubits) ** (gate.angle / np.pi),
            cirq_ops.XX(*qubits),
        ]
    elif isinstance(gate, braket_gates.CPhaseShift01):
        return [
            cirq_ops.X(qubits[0]),
            cirq_ops.CZ.on(*qubits) ** (gate.angle / np.pi),
            cirq_ops.X(qubits[0]),
        ]
    elif isinstance(gate, braket_gates.CPhaseShift10):
        return [
            cirq_ops.X(qubits[1]),
            cirq_ops.CZ.on(*qubits) ** (gate.angle / np.pi),
            cirq_ops.X(qubits[1]),
        ]
    elif isinstance(gate, braket_gates.PSwap):
        return [
            cirq_ops.SWAP.on(*qubits),
            cirq_ops.CNOT.on(*qubits),
            cirq_ops.Z.on(qubits[1]) ** (gate.angle / np.pi),
            cirq_ops.CNOT.on(*qubits),
        ]
    elif isinstance(gate, braket_gates.XX):
        return [cirq_ops.XXPowGate(exponent=gate.angle / np.pi, global_shift=-0.5).on(*qubits)]
    elif isinstance(gate, braket_gates.YY):
        return [cirq_ops.YYPowGate(exponent=gate.angle / np.pi, global_shift=-0.5).on(*qubits)]
    elif isinstance(gate, braket_gates.ZZ):
        return [cirq_ops.ZZPowGate(exponent=gate.angle / np.pi, global_shift=-0.5).on(*qubits)]
    elif isinstance(gate, braket_gates.XY):
        return [cirq_ops.ISwapPowGate(exponent=gate.angle / np.pi).on(*qubits)]

    else:
        try:
            matrix = _gate_to_matrix_braket(gate)
            unitary_gate = _create_unitary_gate_cirq(matrix)
            return [unitary_gate.on(*qubits)]
        except (ValueError, TypeError) as err:
            raise ValueError(f"Unable to convert the instruction {instr} to Cirq.") from err

    return None  # type: ignore[return-value]  # pragma: no cover

# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module containing functions to convert between Cirq's circuit
representation and Qiskit's circuit representation.

"""
from cirq import Circuit, ops as cirq_ops, protocols
from pytket.circuit import Circuit as TKCircuit
from pytket.qasm import circuit_to_qasm_str, circuit_from_qasm_str

from qbraid.interface import convert_to_contiguous
from qbraid.interface.qbraid_cirq.tools import _convert_to_line_qubits
from qbraid.transpiler.cirq_qasm import from_qasm, to_qasm
from qbraid.transpiler.custom_gates import _map_zpow_and_unroll
from qbraid.transpiler.exceptions import CircuitConversionError


def to_pytket(circuit: Circuit) -> TKCircuit:
    """Returns a Qiskit circuit equivalent to the input Cirq circuit. Note
    that the output circuit registers may not match the input circuit
    registers.

    Args:
        circuit: Cirq circuit to convert to a Qiskit circuit.

    Returns:
        PyTket.QuantumCircuit object equivalent to the input Cirq circuit.
    """
    try:
        contig_circuit = convert_to_contiguous(circuit, rev_qubits=False)
        compat_circuit = _map_zpow_and_unroll(contig_circuit)
        return circuit_from_qasm_str(to_qasm(compat_circuit))
    except ValueError as err:
        raise CircuitConversionError("Cirq qasm converter doesn't yet support qasm3.") from err


def from_pytket(circuit: TKCircuit) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Pytket circuit.

    Args:
        circuit: Ptket circuit to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input Pytket circuit.
    """
    try:
        qasm_str = circuit_to_qasm_str(circuit)
        cirq_circuit = from_qasm(qasm_str)
        return _convert_to_line_qubits(cirq_circuit, rev_qubits=False)
    except Exception as err:
        raise CircuitConversionError("Cirq qasm converter doesn't yet support qasm3.") from err

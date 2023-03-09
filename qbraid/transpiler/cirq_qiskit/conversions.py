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
import cirq
import qiskit

from qbraid.interface import convert_to_contiguous
from qbraid.interface.qbraid_cirq.tools import _convert_to_line_qubits
from qbraid.transpiler.cirq_qasm import from_qasm, to_qasm
from qbraid.transpiler.custom_gates import _map_zpow_and_unroll
from qbraid.transpiler.exceptions import CircuitConversionError


def to_qiskit(circuit: cirq.Circuit) -> qiskit.QuantumCircuit:
    """Returns a Qiskit circuit equivalent to the input Cirq circuit. Note
    that the output circuit registers may not match the input circuit
    registers.

    Args:
        circuit: Cirq circuit to convert to a Qiskit circuit.

    Returns:
        Qiskit.QuantumCircuit object equivalent to the input Cirq circuit.
    """
    try:
        contig_circuit = convert_to_contiguous(circuit, rev_qubits=True)
        compat_circuit = _map_zpow_and_unroll(contig_circuit)
        return qiskit.QuantumCircuit.from_qasm_str(to_qasm(compat_circuit))
    except ValueError:
        raise CircuitConversionError(f"cirq's qasm doesn't support qasm3 yet.")


def from_qiskit(circuit: qiskit.QuantumCircuit) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input Qiskit circuit.

    Args:
        circuit: Qiskit circuit to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input Qiskit circuit.
    """
    try:
        qasm_str = circuit.qasm()
        cirq_circuit = from_qasm(qasm_str)
        return _convert_to_line_qubits(cirq_circuit, rev_qubits=True)
    except:
        raise CircuitConversionError(f"cirq's qasm doesn't support qasm3 yet.")

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
Unit tests for the qbraid convert_to_contiguous interfacing

"""
from cirq import LineQubit, Circuit, X, Y, Z
import numpy as np
from braket.circuits import Circuit as BKCircuit
from qiskit import QuantumCircuit
from pytket.circuit import Circuit as TKCircuit

from qbraid.interface.calculate_unitary import circuits_allclose
from qbraid.interface.convert_to_contiguous import convert_to_contiguous


def test_remove_idle_qubits_qiskit():
    """Test convert_to_contigious on qiskit circuit"""
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    contig_circuit = convert_to_contiguous(circuit)
    assert contig_circuit.num_qubits == 2


def test_convert_braket_bell():
    """Test convert_to_contigious on bell circuit"""
    circuit = BKCircuit().h(0).cnot(0, 1)  # pylint: disable=no-member
    h_gate = np.sqrt(1 / 2) * np.array([[1, 1], [1, -1]])
    h_gate_kron = np.kron(np.eye(2), h_gate)
    cnot_gate = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]])
    u_expected = np.einsum("ij,jk->ki", h_gate_kron, cnot_gate)
    contig_circuit = convert_to_contiguous(circuit)
    u_test = contig_circuit.as_unitary()
    assert np.allclose(u_expected, u_test)


def test_compare_conversion_braket_cirq():
    """Test unitary equivalance after converting to contiguous qubits"""
    # pylint: disable=no-member
    braket_circuit = BKCircuit()
    braket_circuit.x(0)
    braket_circuit.y(2)
    braket_circuit.z(4)
    # pylint: enable=no-member
    assert braket_circuit.qubit_count == 3

    cirq_circuit = Circuit()
    q0 = LineQubit(4)
    q2 = LineQubit(2)
    q4 = LineQubit(0)
    cirq_circuit.append(X(q0))
    cirq_circuit.append(Y(q2))
    cirq_circuit.append(Z(q4))
    assert len(cirq_circuit.all_qubits()) == 3

    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)

    braket_compat_circuit = convert_to_contiguous(braket_circuit)
    assert braket_compat_circuit.qubit_count == 3

    cirq_compat_circuit = convert_to_contiguous(cirq_circuit)

    assert circuits_allclose(braket_compat_circuit, cirq_compat_circuit, strict_gphase=True)

    cirq_expanded_circuit = convert_to_contiguous(cirq_circuit, expansion=True)
    assert len(cirq_expanded_circuit.all_qubits()) == 5


def test_remove_blank_wires_pytket():
    circuit = TKCircuit(3)
    circuit.H(0)
    circuit.CX(0, 1)
    contig_circuit = convert_to_contiguous(circuit)
    assert contig_circuit.n_qubits == 2

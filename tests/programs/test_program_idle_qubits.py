# Copyright 2025 qBraid
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
Unit tests for transpiling ciruits with idle qubits

"""
import braket.circuits
import cirq
import pytest
import qiskit

from qbraid.interface.circuit_equality import assert_allclose_up_to_global_phase, circuits_allclose
from qbraid.programs import load_program
from qbraid.transpiler import transpile

# pylint: disable=redefined-outer-name


@pytest.fixture
def braket_circuit() -> braket.circuits.Circuit:
    """Returns Braket bell circuit with idle qubits"""
    return braket.circuits.Circuit().h(4).cnot(4, 8)


@pytest.fixture
def cirq_circuit() -> cirq.Circuit:
    """Returns Cirq bell circuit with idle qubits"""
    q4, q8 = cirq.LineQubit(4), cirq.LineQubit(8)
    circuit = cirq.Circuit(cirq.ops.H(q4), cirq.ops.CNOT(q4, q8))
    return circuit


@pytest.fixture
def qiskit_circuit() -> qiskit.QuantumCircuit:
    """Returns Qiskit bell circuit with idle qubits"""
    circuit = qiskit.QuantumCircuit(9)
    circuit.h(4)
    circuit.cx(4, 8)
    return circuit


def test_braket_to_cirq(braket_circuit):
    """Tests Braket conversions"""
    cirq_test = transpile(braket_circuit, "cirq", require_native=True)
    assert circuits_allclose(cirq_test, braket_circuit)


def test_braket_to_qiskit(braket_circuit):
    """Tests Braket conversions"""
    qiskit_test = transpile(braket_circuit, "qiskit", require_native=True)
    qprogram_qiskit = load_program(qiskit_test)
    qprogram_braket = load_program(braket_circuit)
    qprogram_braket.populate_idle_qubits()
    qiskit_u = qprogram_qiskit.unitary()
    braket_u = qprogram_braket.unitary()
    assert_allclose_up_to_global_phase(qiskit_u, braket_u, atol=1e-7)


def test_cirq_to_braket(cirq_circuit):
    """Tests Cirq conversions"""
    braket_test = transpile(cirq_circuit, "braket", require_native=True)
    assert circuits_allclose(braket_test, cirq_circuit)


def test_cirq_to_qiskit(cirq_circuit):
    """Tests Cirq conversions"""
    qiskit_test = transpile(cirq_circuit, "qiskit", require_native=True)
    assert circuits_allclose(qiskit_test, cirq_circuit)


def test_qiskit_to_cirq(qiskit_circuit):
    """Tests Qiskit conversions"""
    cirq_test = transpile(qiskit_circuit, "cirq", require_native=True)
    qprogram_qiskit = load_program(qiskit_circuit)
    qprogram_cirq = load_program(cirq_test)
    qprogram_cirq.populate_idle_qubits()
    qiskit_u = qprogram_qiskit.unitary()
    cirq_u = qprogram_cirq.unitary()
    assert_allclose_up_to_global_phase(qiskit_u, cirq_u, atol=1e-7)


def test_qiskit_to_braket(qiskit_circuit):
    """Tests Qiskit conversions"""
    braket_test = transpile(qiskit_circuit, "braket", require_native=True)
    qprogram_qiskit = load_program(qiskit_circuit)
    qprogram_braket = load_program(braket_test)
    qprogram_braket.populate_idle_qubits()
    qiskit_u = qprogram_qiskit.unitary()
    braket_u = qprogram_braket.unitary()
    assert_allclose_up_to_global_phase(qiskit_u, braket_u, atol=1e-7)

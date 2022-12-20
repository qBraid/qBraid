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
Unit tests for converting Qiskit circuits to Cirq circuits.

"""
import numpy as np
import pytest
from qiskit import QuantumCircuit

from qbraid.interface import circuits_allclose
from qbraid.transpiler.cirq_qiskit.conversions import from_qiskit


def test_bell_state_from_qiskit():
    """Tests qiskit.QuantumCircuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h(0)
    qiskit_circuit.cx(0, 1)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_common_gates_from_qiskit():
    qiskit_circuit = QuantumCircuit(4)
    qiskit_circuit.h([0, 1, 2, 3])
    qiskit_circuit.x([0, 1])
    qiskit_circuit.y(2)
    qiskit_circuit.z(3)
    qiskit_circuit.s(0)
    qiskit_circuit.sdg(1)
    qiskit_circuit.t(2)
    qiskit_circuit.tdg(3)
    qiskit_circuit.rx(np.pi / 4, 0)
    qiskit_circuit.ry(np.pi / 2, 1)
    qiskit_circuit.rz(3 * np.pi / 4, 2)
    qiskit_circuit.p(np.pi / 8, 3)
    qiskit_circuit.sx(0)
    qiskit_circuit.sxdg(1)
    qiskit_circuit.iswap(2, 3)
    qiskit_circuit.swap([0, 1], [2, 3])
    qiskit_circuit.cx(0, 1)
    qiskit_circuit.cp(np.pi / 4, 2, 3)

    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_u1_gate_from_qiskit():
    qiskit_circuit = QuantumCircuit(1)
    qiskit_circuit.u1(np.pi / 8, 0)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_u2_gate_from_qiskit():
    qiskit_circuit = QuantumCircuit(1)
    qiskit_circuit.u2(np.pi / 8, np.pi / 4, 0)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_u3_gate_from_qiskit():
    qiskit_circuit = QuantumCircuit(1)
    qiskit_circuit.u3(np.pi / 8, np.pi / 4, np.pi / 2, 0)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_cu1_gate_from_qiskit(qubits):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.cu1(np.pi / 8, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_cu3_gate_from_qiskit(qubits):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.cu3(np.pi / 8, np.pi / 4, np.pi / 2, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_crz_gate_from_qiskit(qubits):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.crz(np.pi / 4, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
@pytest.mark.parametrize("theta", (0, 2 * np.pi, np.pi / 2, np.pi / 4))
def test_rzz_gate_from_qiskit(qubits, theta):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.rzz(theta, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_iswap_gate_from_qiskit():
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h([0, 1])
    qiskit_circuit.iswap(0, 1)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)

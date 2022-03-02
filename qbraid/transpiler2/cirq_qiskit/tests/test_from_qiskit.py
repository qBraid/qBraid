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

"""Unit tests for converting Qiskit circuits to Cirq circuits."""
import numpy as np
import pytest
from qiskit import QuantumCircuit

from qbraid.interface2 import equal_unitaries
from qbraid.transpiler2.conversions.cirq_qiskit.conversions import from_qiskit


def test_bell_state_from_qiskit():
    """Tests qiskit.QuantumCircuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h(0)
    qiskit_circuit.cx(0, 1)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert equal_unitaries(qiskit_circuit, cirq_circuit)


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
    assert equal_unitaries(qiskit_circuit, cirq_circuit)


def test_u1_gate_from_qiskit():
    qiskit_circuit = QuantumCircuit(1)
    qiskit_circuit.u1(np.pi / 8, 0)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert equal_unitaries(qiskit_circuit, cirq_circuit)


def test_u2_gate_from_qiskit():
    qiskit_circuit = QuantumCircuit(1)
    qiskit_circuit.u2(np.pi / 8, np.pi / 4, 0)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert equal_unitaries(qiskit_circuit, cirq_circuit)


def test_u3_gate_from_qiskit():
    qiskit_circuit = QuantumCircuit(1)
    qiskit_circuit.u3(np.pi / 8, np.pi / 4, np.pi / 2, 0)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert equal_unitaries(qiskit_circuit, cirq_circuit)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_cu1_gate_from_qiskit(qubits):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.cu1(np.pi / 8, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert equal_unitaries(qiskit_circuit, cirq_circuit)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_cu3_gate_from_qiskit(qubits):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.cu3(np.pi / 8, np.pi / 4, np.pi / 2, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert equal_unitaries(qiskit_circuit, cirq_circuit)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_crz_gate_from_qiskit(qubits):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.crz(np.pi / 4, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert equal_unitaries(qiskit_circuit, cirq_circuit)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
@pytest.mark.parametrize("theta", (0, 2 * np.pi, np.pi / 2, np.pi / 4))
def test_rzz_gate_from_qiskit(qubits, theta):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.rzz(theta, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert equal_unitaries(qiskit_circuit, cirq_circuit)


def test_iswap_gate_from_qiskit():
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h([0, 1])
    qiskit_circuit.iswap(0, 1)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert equal_unitaries(qiskit_circuit, cirq_circuit)
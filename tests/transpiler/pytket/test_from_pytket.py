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
Unit tests for converting pytket circuits to Cirq circuits.

"""
import pytest

try:
    import numpy as np
    from pytket.circuit import Circuit as TKCircuit

    from qbraid.interface import circuits_allclose, random_circuit
    from qbraid.transpiler import ConversionGraph, transpile

    pytket_not_installed = False
except ImportError:
    pytket_not_installed = True

pytestmark = pytest.mark.skipif(pytket_not_installed, reason="pytket not installed")


def test_bell_state_from_qiskit():
    """Tests pytket.circuit.Circuit --> cirq.Circuit
    with a Bell state circuit."""
    pytket_circuit = TKCircuit(2)
    pytket_circuit.H(0)
    pytket_circuit.CX(0, 1)
    cirq_circuit = transpile(pytket_circuit, "cirq")
    assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_crz_gate_from_pytket(qubits):
    """Test converting controlled Rz gate from pytket to cirq."""
    pytket_circuit = TKCircuit(2)
    pytket_circuit.CRz(np.pi / 4, *qubits)
    cirq_circuit = transpile(pytket_circuit, "cirq")
    assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
@pytest.mark.parametrize("theta", (0, 2 * np.pi, np.pi / 2, np.pi / 4))
def test_rzz_gate_from_pytket(qubits, theta):
    """Test converting Rzz gate from pytket to cirq."""
    pytket_circuit = TKCircuit(2)
    pytket_circuit.ZZPhase(theta, *qubits)
    cirq_circuit = transpile(pytket_circuit, "cirq")
    assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)


def test_100_random_pytket():
    """Test converting 100 random pytket circuits to cirq."""
    graph = ConversionGraph(nodes=["pytket", "cirq", "qasm2"])
    for _ in range(100):
        pytket_circuit = random_circuit("pytket", 4, 1, graph=graph)
        cirq_circuit = transpile(pytket_circuit, "cirq")
        assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=False)

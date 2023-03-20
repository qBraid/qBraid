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
Unit tests for converting pytket circuits to Cirq circuits.

"""
import numpy as np
import pytest
from cirq import Circuit, LineQubit, ops, protocols
from pytket.circuit import Circuit as TKCircuit
from pytket.circuit import OpType
from pytket.qasm import circuit_to_qasm_str

from qbraid.interface import circuits_allclose, convert_to_contiguous, random_circuit
from qbraid.transpiler.cirq_pytket.convert_pytket_qasm import from_pytket
from qbraid.transpiler.exceptions import CircuitConversionError


def test_bell_state_from_qiskit():
    """Tests pytket.circuit.Circuit --> cirq.Circuit
    with a Bell state circuit.
    """
    pytket_circuit = TKCircuit(2)
    pytket_circuit.H(0)
    pytket_circuit.CX(0, 1)
    cirq_circuit = from_pytket(pytket_circuit)
    assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)


# todo: pytket_shared15


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_crz_gate_from_pytket(qubits):
    pytket_circuit = TKCircuit(2)
    pytket_circuit.CRz(np.pi / 4, *qubits)
    cirq_circuit = from_pytket(pytket_circuit)
    assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
@pytest.mark.parametrize("theta", (0, 2 * np.pi, np.pi / 2, np.pi / 4))
def test_rzz_gate_from_pytket(qubits, theta):
    pytket_circuit = TKCircuit(2)
    pytket_circuit.ZZPhase(theta, *qubits)
    cirq_circuit = from_pytket(pytket_circuit)
    assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)


# todo: iswap gate, roundtrip, noncontig


def test_100_random_pytket():
    for _ in range(100):
        pytket_circuit = random_circuit("pytket", 4, 1)
        cirq_circuit = from_pytket(pytket_circuit)
        assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=False)


def test_raise_error():
    with pytest.raises(CircuitConversionError):
        pytket_circuit = TKCircuit(2)
        pytket_circuit.ISWAPMax(0, 1)
        cirq_circuit = from_pytket(pytket_circuit)

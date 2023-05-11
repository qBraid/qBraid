# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# fmt: off

"""
Unit tests for converting pytket circuits to Cirq circuits.

"""
import numpy as np
import pytest
# from cirq import Circuit, LineQubit, ops, protocols
from pytket.circuit import Circuit as TKCircuit

from qbraid.interface import circuits_allclose, random_circuit
from qbraid.transpiler.cirq_pytket.conversions import from_pytket
from qbraid.transpiler.exceptions import CircuitConversionError

# from pytket.circuit import OpType
# from pytket.qasm import circuit_to_qasm_str


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

# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for conversions between Amazon Braket circuits and Qiskit circuits
using OpenQASM 3.

"""
import numpy as np
from braket.circuits import Circuit

from qbraid.interface import circuits_allclose
from qbraid.transpiler.cirq_braket.braket_qasm import braket_to_qasm3
from qbraid.transpiler.qiskit_braket.conversions import braket_to_qiskit


def test_one_qubit_circuit_to_qiskit():
    braket_circuit = Circuit().h(0).ry(0, np.pi / 2)
    qiskit_circuit = braket_to_qiskit(braket_circuit)
    assert circuits_allclose(braket_circuit, qiskit_circuit, strict_gphase=True)


def test_two_qubit_circuit_to_qiskit():
    braket_circuit = Circuit().h(0).cnot(0, 1)
    qiskit_circuit = braket_to_qiskit(braket_circuit)
    assert circuits_allclose(braket_circuit, qiskit_circuit, strict_gphase=True)


def test_braket_to_qiskit_stdgates():
    """Test converting braket to qiskit for standard gates."""
    circuit = Circuit()

    circuit.h([0, 1, 2, 3])
    circuit.x([0, 1])
    circuit.y(2)
    circuit.z(3)
    circuit.s(0)
    circuit.si(1)
    circuit.t(2)
    circuit.ti(3)
    circuit.rx(0, np.pi / 4)
    circuit.ry(1, np.pi / 2)
    circuit.rz(2, 3 * np.pi / 4)
    circuit.phaseshift(3, np.pi / 8)
    circuit.v(0)
    # circuit.vi(1)
    circuit.iswap(2, 3)
    circuit.swap(0, 2)
    circuit.swap(1, 3)
    circuit.cnot(0, 1)
    circuit.cphaseshift(2, 3, np.pi / 4)

    qiskit_circuit = braket_to_qiskit(circuit)
    assert circuits_allclose(circuit, qiskit_circuit, strict_gphase=True)


def test_braket_to_qiskit_vi_sxdg():
    """Test converting braket to qiskit with vi/sxdg gate with non-strict global phase comparison."""
    circuit = Circuit().vi(0)
    qiskit_circuit = braket_to_qiskit(circuit)
    assert circuits_allclose(circuit, qiskit_circuit, strict_gphase=False)

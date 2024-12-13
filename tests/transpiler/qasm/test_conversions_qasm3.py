# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for OpenQASM 3 conversions

"""
import braket.circuits
import numpy as np
import qiskit

from qbraid.interface import circuits_allclose
from qbraid.transpiler.converter import transpile


def test_one_qubit_qiskit_to_braket():
    """Test converting qiskit to braket for one qubit circuit."""
    qiskit_circuit = qiskit.QuantumCircuit(1)
    qiskit_circuit.h(0)
    qiskit_circuit.ry(np.pi / 2, 0)
    qasm3_program = transpile(qiskit_circuit, "qasm3")
    braket_circuit = transpile(qasm3_program, "braket")
    circuits_allclose(qiskit_circuit, braket_circuit, strict_gphase=True)


def test_one_qubit_braket_to_qiskit():
    """Test converting braket to qiskit for one qubit circuit."""
    braket_circuit = braket.circuits.Circuit().h(0).ry(0, np.pi / 2)
    qasm3_program = transpile(braket_circuit, "qasm3")
    qiskit_circuit = transpile(qasm3_program, "qiskit")
    assert circuits_allclose(braket_circuit, qiskit_circuit, strict_gphase=True)


def test_two_qubit_braket_to_qiskit():
    """Test converting braket to qiskit for two qubit circuit."""
    braket_circuit = braket.circuits.Circuit().h(0).cnot(0, 1)
    qasm3_program = transpile(braket_circuit, "qasm3")
    qiskit_circuit = transpile(qasm3_program, "qiskit")
    assert circuits_allclose(braket_circuit, qiskit_circuit, strict_gphase=True)


def test_braket_to_qiskit_stdgates():
    """Test converting braket to qiskit for standard gates."""
    circuit = braket.circuits.Circuit()

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
    circuit.vi(1)
    circuit.iswap(2, 3)
    circuit.swap(0, 2)
    circuit.swap(1, 3)
    circuit.cnot(0, 1)
    circuit.cphaseshift(2, 3, np.pi / 4)

    cirq_circuit = transpile(circuit, "cirq")
    qasm3_program = transpile(circuit, "qasm3")
    qasm2_program = transpile(cirq_circuit, "qasm2")
    qiskit_circuit_1 = transpile(qasm3_program, "qiskit")
    qiskit_circuit_2 = transpile(qasm2_program, "qiskit")
    assert circuits_allclose(circuit, qiskit_circuit_1, strict_gphase=False)
    assert circuits_allclose(circuit, qiskit_circuit_2, strict_gphase=False)


def test_braket_to_qiskit_vi_sxdg():
    """Test converting braket to qiskit with vi/sxdg gate with
    non-strict global phase comparison."""
    circuit = braket.circuits.Circuit().vi(0)
    qasm3_program = transpile(circuit, "qasm3")
    qiskit_circuit = transpile(qasm3_program, "qiskit")
    assert circuits_allclose(circuit, qiskit_circuit, strict_gphase=False)

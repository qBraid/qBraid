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
Unit tests for converting Cirq circuits with MeasurementGate(s) to Braket circuits

"""
import cirq

from qbraid.interface import circuits_allclose
from qbraid.transpiler.cirq_braket.convert_to_braket import to_braket


def alpha_pump(sys, env):
    yield cirq.CNOT(sys[0], env[0])
    yield cirq.H(sys[1])
    yield cirq.X(env[1])


def beta_pump(sys, env):
    yield cirq.CNOT(sys[1], sys[0])
    yield cirq.X(env[0])


def batch_circuit():
    sys_qubits = [cirq.LineQubit(i) for i in range(0, 6)]
    env_qubits = [cirq.LineQubit(i) for i in range(6, 11)]

    circuit = cirq.Circuit()
    circuit += alpha_pump(sys_qubits[0:2], env_qubits[0:2])
    circuit += alpha_pump(sys_qubits[2:4], env_qubits[2:4])
    circuit += beta_pump(sys_qubits[4:6], env_qubits[4:5])
    circuit.append(cirq.measure(*circuit.all_qubits()))
    return circuit


def test_ommit_measurement_gate():
    """Test that cirq.MeasurementGate is skipped during Braket conversion"""
    cirq_circuit = batch_circuit()
    braket_circuit = to_braket(cirq_circuit)
    assert circuits_allclose(cirq_circuit, braket_circuit)

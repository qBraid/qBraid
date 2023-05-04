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

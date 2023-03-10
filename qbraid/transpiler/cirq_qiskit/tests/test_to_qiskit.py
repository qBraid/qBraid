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
Unit tests for conversions between Cirq circuits and Qiskit circuits.

"""
import numpy as np
import pytest
from cirq import LineQubit, Circuit, ops, testing

from qbraid.interface import circuits_allclose
from qbraid.transpiler.cirq_qiskit.conversions import to_qiskit
from qbraid.transpiler.exceptions import CircuitConversionError


def test_bell_state_to_qiskit():
    """Tests Circuit --> qiskit.QuantumCircuit --> Circuit
    with a Bell state circuit.
    """
    qreg = LineQubit.range(2)
    cirq_circuit = Circuit([ops.H.on(qreg[0]), ops.CNOT.on(qreg[0], qreg[1])])
    qiskit_circuit = to_qiskit(cirq_circuit)
    print()
    print(cirq_circuit)
    print()
    print(qiskit_circuit)
    print()
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5])
def test_random_circuit_to_qiskit(num_qubits):
    for i in range(10):
        cirq_circuit = testing.random_circuit(
            qubits=num_qubits,
            n_moments=np.random.randint(1, 6),
            op_density=1,
            random_state=np.random.randint(1, 10),
        )
        qiskit_circuit = to_qiskit(cirq_circuit)
        equal = circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)
        if not equal:
            print(qiskit_circuit)
            assert False
        else:
            assert True


def test_raise_error():
    with pytest.raises(CircuitConversionError):
        probs = np.random.uniform(low=0, high=0.5)
        cirq_circuit = Circuit(ops.PhaseDampingChannel(probs).on(*LineQubit.range(1)))
        to_qiskit(cirq_circuit)

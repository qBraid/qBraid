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
Unit tests for conversions between Cirq circuits and pytket circuits.

"""
import numpy as np
import pytest
from cirq import Circuit, ops, LineQubit, testing
from pytket.circuit import Circuit as TKCircuit
from pytket.qasm import circuit_to_qasm_str

from qbraid.interface import circuits_allclose
from qbraid.interface.qbraid_cirq._utils import _equal
from qbraid.transpiler.cirq_qasm import from_qasm
from qbraid.transpiler.cirq_pytket.convert_pytket_qasm import from_pytket, to_pytket


def test_bell_state_to_from_circuits():
    """Tests cirq.Circuit --> pytket.circuit.Circuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qreg = LineQubit.range(2)
    cirq_circuit = Circuit([ops.H.on(qreg[0]), ops.CNOT.on(qreg[0], qreg[1])])
    qiskit_circuit = to_pytket(cirq_circuit)  # Qiskit from Cirq
    circuit_cirq = from_pytket(qiskit_circuit)  # Cirq from Qiskit
    assert np.allclose(cirq_circuit.unitary(), circuit_cirq.unitary())


def test_random_circuit_to_from_circuits():
    """Tests cirq.Circuit --> qiskit.QuantumCircuit --> cirq.Circuit
    with a random two-qubit circuit.
    """
    cirq_circuit = testing.random_circuit(qubits=2, n_moments=10, op_density=0.99, random_state=1)
    qiskit_circuit = to_pytket(cirq_circuit)
    circuit_cirq = from_pytket(qiskit_circuit)
    assert np.allclose(cirq_circuit.unitary(), circuit_cirq.unitary())


@pytest.mark.parametrize("as_qasm", (True, False))
def test_convert_with_barrier(as_qasm):
    """Tests converting a pytket circuit with a barrier to a Cirq circuit."""
    n = 5
    pytket_circuit = TKCircuit(n)
    pytket_circuit.add_barrier([i for i in range(n)])

    if as_qasm:
        cirq_circuit = from_qasm(circuit_to_qasm_str(pytket_circuit))
    else:
        cirq_circuit = from_pytket(pytket_circuit)

    assert _equal(cirq_circuit, Circuit())


@pytest.mark.parametrize("as_qasm", (True, False))
def test_convert_with_multiple_barriers(as_qasm):
    """Tests converting a Qiskit circuit with barriers to a Cirq circuit."""
    n = 1
    num_ops = 10

    pytket_circuit = TKCircuit(n)
    for _ in range(num_ops):
        for i in range(n):
            pytket_circuit.H(i)
        pytket_circuit.add_barrier([i for i in range(n)])

    if as_qasm:
        cirq_circuit = from_qasm(circuit_to_qasm_str(pytket_circuit))
    else:
        cirq_circuit = from_pytket(pytket_circuit)

    qbit = LineQubit(0)
    correct = Circuit(ops.H.on(qbit) for _ in range(num_ops))
    assert _equal(cirq_circuit, correct)
    assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)

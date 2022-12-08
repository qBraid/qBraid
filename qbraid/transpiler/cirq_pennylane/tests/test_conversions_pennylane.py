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
Unit tests for Pennylane <-> Cirq conversions.

"""
import cirq
import numpy as np
import pennylane as qml
import pytest

from qbraid.interface import circuits_allclose
from qbraid.interface.qbraid_cirq._utils import _equal
from qbraid.transpiler.cirq_pennylane.conversions import (
    UnsupportedQuantumTapeError,
    from_pennylane,
    to_pennylane,
)


def test_from_pennylane():
    with qml.tape.QuantumTape() as tape:
        qml.CNOT(wires=[0, 1])

    circuit = from_pennylane(tape)
    correct = cirq.Circuit(cirq.CNOT(*cirq.LineQubit.range(2)))

    assert _equal(circuit, correct, require_qubit_equality=False)


def test_from_pennylane_unsupported_tapes():
    with qml.tape.QuantumTape() as tape:
        qml.CZ(wires=[0, "a"])

    with pytest.raises(UnsupportedQuantumTapeError, match="could not sort"):
        from_pennylane(tape)


def test_no_variance():
    with qml.tape.QuantumTape() as tape:
        qml.CNOT(wires=[0, 1])
        qml.expval(qml.PauliZ(0))

    with pytest.raises(
        UnsupportedQuantumTapeError,
        match="Measurements are not supported on the input tape.",
    ):
        from_pennylane(tape)


@pytest.mark.parametrize("random_state", range(10))
def test_to_from_pennylane(random_state):
    circuit = cirq.testing.random_circuit(
        qubits=4, n_moments=2, op_density=1, random_state=random_state
    )

    converted = from_pennylane(to_pennylane(circuit))
    # Gates (e.g. iSWAP) aren't guaranteed to be preserved. Check unitary
    # instead of circuit equality.
    assert circuits_allclose(converted, circuit)


def test_to_from_pennylane_cnot_same_gates():
    qreg = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.CNOT(*qreg))
    converted = from_pennylane(to_pennylane(circuit))
    assert _equal(circuit, converted, require_qubit_equality=False)


def test_to_from_pennylane_identity():
    q = cirq.LineQubit(0)
    # Empty circuit
    circuit = cirq.Circuit()
    converted = from_pennylane(to_pennylane(circuit))
    assert _equal(circuit, converted, require_qubit_equality=False)
    circuit = cirq.Circuit(cirq.I(q))
    # Identity gate
    converted = from_pennylane(to_pennylane(circuit))
    # TODO: test circuit equality after Identity operation will be added
    # to PennyLane (https://github.com/PennyLaneAI/pennylane/issues/1632)
    assert np.allclose(cirq.unitary(circuit), cirq.unitary(converted))


def test_non_consecutive_wires_error():
    with qml.tape.QuantumTape() as tape:
        qml.CNOT(wires=[0, 2])
    with pytest.raises(
        UnsupportedQuantumTapeError,
        match="contiguously pack",
    ):
        from_pennylane(tape)

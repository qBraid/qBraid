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
Unit tests for Cirq utility functions.

"""
from copy import deepcopy

import cirq
import pytest

from qbraid.interface.circuit_equality import _equal


@pytest.mark.parametrize("require_qubit_equality", [True, False])
def test_circuit_equality_identical_qubits(require_qubit_equality):
    """Test evaluating circuit equality with added qubit equality requirement for
    circuit constructed using the same qubits."""
    qreg = cirq.NamedQubit.range(5, prefix="q_")
    circA = cirq.Circuit(cirq.ops.H.on_each(*qreg))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qreg))
    assert circA is not circB
    assert _equal(circA, circB, require_qubit_equality=require_qubit_equality)


@pytest.mark.parametrize("require_qubit_equality", [True, False])
def test_circuit_equality_nonidentical_but_equal_qubits(
    require_qubit_equality,
):
    """Test evaluating circuit equality with added qubit equality requirement for
    circuit constructed with independent qubit declarations."""
    n = 5
    qregA = cirq.NamedQubit.range(n, prefix="q_")
    qregB = cirq.NamedQubit.range(n, prefix="q_")
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert circA is not circB
    assert _equal(circA, circB, require_qubit_equality=require_qubit_equality)


def test_circuit_equality_linequbit_gridqubit_equal_indices():
    """Test evaluating circuit equality for circuits constructed
    using LineQubit and GridQubit with identical qubit indexing."""
    n = 10
    qregA = cirq.LineQubit.range(n)
    qregB = [cirq.GridQubit(x, 0) for x in range(n)]
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)


def test_circuit_equality_linequbit_gridqubit_unequal_indices():
    """Test evaluating circuit equality for circuits constructed
    using LineQubit and GridQubit with differing qubit indexing."""
    n = 10
    qregA = cirq.LineQubit.range(n)
    qregB = [cirq.GridQubit(x + 3, 0) for x in range(n)]
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)


def test_circuit_equality_linequbit_namedqubit_equal_indices():
    """Test evaluating circuit equality for circuits constructed
    using LineQubit and NamedQubit with identical qubit indexing."""
    n = 8
    qregA = cirq.LineQubit.range(n)
    qregB = cirq.NamedQubit.range(n, prefix="q_")
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)


def test_circuit_equality_linequbit_namedqubit_unequal_indices():
    """Test evaluating circuit equality for circuits constructed
    using LineQubit and NamedQubit with differing qubit indexing."""
    n = 11
    qregA = cirq.LineQubit.range(n)
    qregB = [cirq.NamedQubit(str(x + 10)) for x in range(n)]
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)


def test_circuit_equality_gridqubit_namedqubit_equal_indices():
    """Test evaluating circuit equality for circuits constructed
    using GridQubit and NamedQubit with identical qubit indexing."""
    n = 8
    qregA = [cirq.GridQubit(0, x) for x in range(n)]
    qregB = cirq.NamedQubit.range(n, prefix="q_")
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)


def test_circuit_equality_gridqubit_namedqubit_unequal_indices():
    """Test evaluating circuit equality for circuits constructed
    using GridQubit and NamedQubit with differing qubit indexing."""
    n = 5
    qregA = [cirq.GridQubit(x + 2, 0) for x in range(n)]
    qregB = [cirq.NamedQubit(str(x + 10)) for x in range(n)]
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)


def test_circuit_equality_unequal_measurement_keys_terminal_measurements():
    """Test evaluating circuit equality for circuits with terminal
    measurement constructed using differing measurement keys."""
    base_circuit = cirq.testing.random_circuit(
        qubits=5, n_moments=10, op_density=0.99, random_state=1
    )
    qreg = list(base_circuit.all_qubits())

    circ1 = deepcopy(base_circuit)
    circ1.append(cirq.measure(q, key="one") for q in qreg)

    circ2 = deepcopy(base_circuit)
    circ2.append(cirq.measure(q, key="two") for q in qreg)

    assert _equal(circ1, circ2, require_measurement_equality=False)
    assert not _equal(circ1, circ2, require_measurement_equality=True)


@pytest.mark.parametrize("require_measurement_equality", [True, False])
def test_circuit_equality_equal_measurement_keys_terminal_measurements(
    require_measurement_equality,
):
    """Test evaluating circuit equality for circuits with terminal
    measurement constructed using identical measurement keys."""
    base_circuit = cirq.testing.random_circuit(
        qubits=5, n_moments=10, op_density=0.99, random_state=1
    )
    qreg = list(base_circuit.all_qubits())

    circ1 = deepcopy(base_circuit)
    circ1.append(cirq.measure(q, key="z") for q in qreg)

    circ2 = deepcopy(base_circuit)
    circ2.append(cirq.measure(q, key="z") for q in qreg)

    assert _equal(
        circ1,
        circ2,
        require_measurement_equality=require_measurement_equality,
    )


def test_circuit_equality_unequal_measurement_keys_nonterminal_measurements():
    """Test evaluating circuit equality for circuits with non-terminal
    measurement constructed using differing measurement keys."""
    base_circuit = cirq.testing.random_circuit(
        qubits=5, n_moments=10, op_density=0.99, random_state=1
    )
    end_circuit = cirq.testing.random_circuit(
        qubits=5, n_moments=5, op_density=0.99, random_state=2
    )
    qreg = list(base_circuit.all_qubits())

    circ1 = deepcopy(base_circuit)
    circ1.append(cirq.measure(q, key="one") for q in qreg)
    circ1 += end_circuit

    circ2 = deepcopy(base_circuit)
    circ2.append(cirq.measure(q, key="two") for q in qreg)
    circ2 += end_circuit

    assert _equal(circ1, circ2, require_measurement_equality=False)
    assert not _equal(circ1, circ2, require_measurement_equality=True)


@pytest.mark.parametrize("require_measurement_equality", [True, False])
def test_circuit_equality_equal_measurement_keys_nonterminal_measurements(
    require_measurement_equality,
):
    """Test evaluating circuit equality for circuits with non-terminal
    measurement constructed using identical measurement keys."""
    base_circuit = cirq.testing.random_circuit(
        qubits=5, n_moments=10, op_density=0.99, random_state=1
    )
    end_circuit = cirq.testing.random_circuit(
        qubits=5, n_moments=5, op_density=0.99, random_state=2
    )
    qreg = list(base_circuit.all_qubits())

    circ1 = deepcopy(base_circuit)
    circ1.append(cirq.measure(q, key="z") for q in qreg)
    circ1 += end_circuit

    circ2 = deepcopy(base_circuit)
    circ2.append(cirq.measure(q, key="z") for q in qreg)
    circ2 += end_circuit

    assert _equal(
        circ1,
        circ2,
        require_measurement_equality=require_measurement_equality,
    )

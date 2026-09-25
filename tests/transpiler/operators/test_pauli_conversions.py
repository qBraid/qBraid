# Copyright 2026 qBraid
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
Tests for conversions between the Pauli-operator types.

Pauli strings form a basis, so two operators are equal exactly when their terms agree;
comparing term dictionaries checks every conversion without building dense matrices.

"""
# Each library is optional, so it is imported only after pytest.importorskip has run.
# pylint: disable=import-outside-toplevel
# cudaq.spin's members are pybind functions pylint cannot see.
# pylint: disable=no-member
from __future__ import annotations

import itertools

import pytest

from qbraid import transpile
from qbraid.transpiler.conversions import _pauli_io
from qbraid.transpiler.exceptions import ConversionPathNotFoundError, ProgramConversionError

CANONICAL = [
    "qiskit_pauli",
    "openfermion_qubit",
    "cirq_pauli",
    "pennylane_pauli",
    "braket_observable",
    "cudaq_spin",
]
LIBRARY = {
    "qiskit_pauli": "qiskit",
    "openfermion_qubit": "openfermion",
    "cirq_pauli": "cirq",
    "pennylane_pauli": "pennylane",
    "braket_observable": "braket",
    "cudaq_spin": "cudaq",
}

# 0.5 X0 Z1 - 1.25i Y1 Y2 + 2 Z2 + 0.3 I, written once per library below.
EXPECTED = {
    frozenset({(0, "X"), (1, "Z")}): 0.5,
    frozenset({(1, "Y"), (2, "Y")}): -1.25j,
    frozenset({(2, "Z")}): 2.0,
    frozenset(): 0.3,
}


def build(alias):
    """The EXPECTED operator in the given library's own type."""
    pytest.importorskip(LIBRARY[alias])
    if alias == "qiskit_pauli":
        from qiskit.quantum_info import SparsePauliOp

        return SparsePauliOp.from_list([("IZX", 0.5), ("YYI", -1.25j), ("ZII", 2.0), ("III", 0.3)])
    if alias == "openfermion_qubit":
        from openfermion import QubitOperator

        return (
            QubitOperator("X0 Z1", 0.5)
            + QubitOperator("Y1 Y2", -1.25j)
            + QubitOperator("Z2", 2.0)
            + QubitOperator((), 0.3)
        )
    if alias == "cirq_pauli":
        import cirq

        q = cirq.LineQubit.range(3)
        return (
            0.5 * cirq.X(q[0]) * cirq.Z(q[1])
            - 1.25j * cirq.Y(q[1]) * cirq.Y(q[2])
            + 2.0 * cirq.Z(q[2])
            + 0.3 * cirq.PauliString()
        )
    if alias == "braket_observable":
        from braket.circuits.observables import I, X, Y, Z

        return 0.5 * X(0) @ Z(1) - 1.25j * Y(1) @ Y(2) + 2.0 * Z(2) + 0.3 * I(0)
    if alias == "cudaq_spin":
        from cudaq import spin

        return (
            0.5 * spin.x(0) * spin.z(1)
            - 1.25j * spin.y(1) * spin.y(2)
            + 2.0 * spin.z(2)
            + 0.3 * spin.i(0)
        )
    from pennylane.pauli import PauliSentence, PauliWord

    return PauliSentence(
        {
            PauliWord({0: "X", 1: "Z"}): 0.5,
            PauliWord({1: "Y", 2: "Y"}): -1.25j,
            PauliWord({2: "Z"}): 2.0,
            PauliWord({}): 0.3,
        }
    )


def terms(alias, op):
    """An operator's terms as {frozenset((qubit, pauli)): coefficient}, zeros dropped."""
    out = {}
    for paulis, coeff in getattr(_pauli_io, f"read_{alias}")(op).terms:
        key = frozenset(paulis.items())
        out[key] = out.get(key, 0) + coeff
    return {k: v for k, v in out.items() if abs(v) > 1e-12}


def assert_same(actual, expected):
    """Same terms, coefficients equal to tolerance."""
    assert actual.keys() == expected.keys()
    for key, value in expected.items():
        assert actual[key] == pytest.approx(value)


@pytest.mark.parametrize("alias", CANONICAL)
def test_fixture_matches_expected(alias):
    """Every hand-written fixture describes the same operator, so the pairs below compare
    like with like."""
    assert_same(terms(alias, build(alias)), EXPECTED)


@pytest.mark.parametrize(("source", "target"), list(itertools.permutations(CANONICAL, 2)))
def test_every_pair_converts_in_one_hop_and_preserves_the_operator(source, target):
    """Each direct conversion, and its return trip, keeps every term and coefficient."""
    op = build(source)
    pytest.importorskip(LIBRARY[target])
    result = transpile(op, target)
    assert_same(terms(target, result), EXPECTED)
    assert_same(terms(source, transpile(result, source)), EXPECTED)


def test_qiskit_labels_are_little_endian():
    """ "XZ" is Z on qubit 0 and X on qubit 1: the physical qubit, not the label position."""
    pytest.importorskip("qiskit")
    of = pytest.importorskip("openfermion")
    from qiskit.quantum_info import SparsePauliOp

    assert transpile(SparsePauliOp("XZ"), "openfermion_qubit") == of.QubitOperator("Z0 X1")


def test_qiskit_width_comes_from_the_highest_qubit_when_unrecorded():
    """Libraries without a width drop trailing identities; that is documented, not guessed."""
    pytest.importorskip("qiskit")
    pytest.importorskip("openfermion")
    from qiskit.quantum_info import SparsePauliOp

    result = transpile(transpile(SparsePauliOp("IIZ"), "openfermion_qubit"), "qiskit_pauli")
    assert result.num_qubits == 1


def test_identity_only_and_zero_operators():
    """An operator acting on no qubit still becomes a valid 1-qubit ``SparsePauliOp``."""
    pytest.importorskip("qiskit")
    of = pytest.importorskip("openfermion")

    identity = transpile(of.QubitOperator((), 2.5), "qiskit_pauli")
    assert identity.num_qubits == 1 and identity.to_list() == [("I", 2.5)]
    assert transpile(of.QubitOperator(), "qiskit_pauli").num_qubits == 1


def test_duplicate_terms_are_summed():
    """Repeated labels are added, not overwritten."""
    pytest.importorskip("qiskit")
    of = pytest.importorskip("openfermion")
    from qiskit.quantum_info import SparsePauliOp

    op = SparsePauliOp.from_list([("XX", 1.0), ("XX", 2.0)])
    assert transpile(op, "openfermion_qubit") == of.QubitOperator("X0 X1", 3.0)


@pytest.mark.parametrize(
    ("case", "match"),
    [
        ("qiskit_parameter", "numeric coefficients"),
        ("openfermion_sympy", "numeric coefficients"),
        ("cirq_grid_qubit", "not a non-negative integer"),
        ("pennylane_string_wire", "not a non-negative integer"),
        ("pennylane_rotation", "no Pauli representation"),
        ("braket_untargeted", "no qubit targets"),
        ("braket_hadamard", "not a Pauli operator"),
        ("cudaq_parameterised", "parameterised coefficient"),
    ],
)
def test_ambiguous_operators_are_refused(case, match):
    """Symbolic coefficients and qubits with no integer index raise instead of guessing."""
    if case == "qiskit_parameter":
        pytest.importorskip("openfermion")
        qiskit = pytest.importorskip("qiskit")
        op, target = (
            qiskit.quantum_info.SparsePauliOp(["X"], [qiskit.circuit.Parameter("t")]),
            "openfermion_qubit",
        )
    elif case == "openfermion_sympy":
        pytest.importorskip("qiskit")
        of, sympy = pytest.importorskip("openfermion"), pytest.importorskip("sympy")
        op, target = of.QubitOperator("X0", sympy.Symbol("t")), "qiskit_pauli"
    elif case == "cirq_grid_qubit":
        pytest.importorskip("openfermion")
        cirq = pytest.importorskip("cirq")
        op, target = (
            cirq.PauliSum.from_pauli_strings([cirq.X(cirq.GridQubit(0, 1))]),
            "openfermion_qubit",
        )
    elif case == "pennylane_string_wire":
        pytest.importorskip("openfermion")
        pytest.importorskip("pennylane")
        from pennylane.pauli import PauliSentence, PauliWord

        op, target = PauliSentence({PauliWord({"a": "X"}): 1.0}), "openfermion_qubit"
    elif case == "pennylane_rotation":
        pytest.importorskip("openfermion")
        qml = pytest.importorskip("pennylane")
        op, target = qml.RX(0.3, 0), "openfermion_qubit"
    elif case == "braket_untargeted":
        pytest.importorskip("openfermion")
        pytest.importorskip("braket")
        from braket.circuits.observables import X, Z

        op, target = 0.5 * X() @ Z(), "openfermion_qubit"
    elif case == "braket_hadamard":
        pytest.importorskip("openfermion")
        pytest.importorskip("braket")
        from braket.circuits.observables import H

        op, target = H(0), "openfermion_qubit"
    else:
        pytest.importorskip("openfermion")
        cudaq = pytest.importorskip("cudaq")
        op = cudaq.ScalarOperator(lambda theta: theta) * cudaq.spin.x(0) + cudaq.spin.z(1)
        target = "openfermion_qubit"
    with pytest.raises(ProgramConversionError, match=match):
        transpile(op, target)


@pytest.mark.parametrize(
    ("case", "target"),
    [
        ("cirq_pauli_string", "openfermion_qubit"),
        ("pennylane_op", "openfermion_qubit"),
        ("qiskit_observable", "openfermion_qubit"),
        ("cudaq_spin_term", "openfermion_qubit"),
    ],
)
def test_types_users_hold_convert_through_their_canonical_form(case, target):
    """``PauliString``, PennyLane operator arithmetic and ``SparseObservable`` all convert."""
    of = pytest.importorskip("openfermion")
    if case == "cirq_pauli_string":
        cirq = pytest.importorskip("cirq")
        q = cirq.LineQubit.range(2)
        op, expected = 0.5 * cirq.X(q[0]) * cirq.Z(q[1]), of.QubitOperator("X0 Z1", 0.5)
    elif case == "pennylane_op":
        qml = pytest.importorskip("pennylane")
        op, expected = qml.X(0) @ qml.Z(1) + 0.5 * qml.Y(0), of.QubitOperator(
            "X0 Z1"
        ) + of.QubitOperator("Y0", 0.5)
    elif case == "cudaq_spin_term":
        cudaq = pytest.importorskip("cudaq")
        op, expected = 0.5 * cudaq.spin.x(0) * cudaq.spin.z(1), of.QubitOperator("X0 Z1", 0.5)
    else:
        qiskit = pytest.importorskip("qiskit")
        # "+" on qubit 0 is (I + X)/2, so "X+" = 0.5 X1 + 0.5 X0 X1.
        op = qiskit.quantum_info.SparseObservable("X+")
        expected = of.QubitOperator("X1", 0.5) + of.QubitOperator("X0 X1", 0.5)
    assert transpile(op, target) == expected


def test_operators_and_circuits_never_convert_into_each_other():
    """Operators are not programs: no path joins them to a circuit in either direction."""
    cirq = pytest.importorskip("cirq")
    pytest.importorskip("qiskit")
    from qiskit.quantum_info import SparsePauliOp

    with pytest.raises(ConversionPathNotFoundError):
        transpile(SparsePauliOp("XZ"), "qasm2")
    with pytest.raises(ConversionPathNotFoundError):
        transpile(cirq.Circuit(cirq.X(cirq.LineQubit(0))), "qiskit_pauli")


def test_braket_identity_and_zero_are_written_on_qubit_zero():
    """Braket has no empty sum and every factor needs a qubit, so these land on qubit 0."""
    pytest.importorskip("braket")
    of = pytest.importorskip("openfermion")
    from braket.circuits.observables import I

    identity = transpile(of.QubitOperator((), 2.5), "braket_observable")
    assert isinstance(identity, I) and identity.coefficient == 2.5 and list(identity.targets) == [0]
    zero = transpile(of.QubitOperator(), "braket_observable")
    assert zero.coefficient == 0


def test_cudaq_result_is_a_spin_operator_even_for_one_term():
    """A one-term result must stay a ``SpinOperator`` or it no longer matches its alias."""
    cudaq = pytest.importorskip("cudaq")
    of = pytest.importorskip("openfermion")

    assert isinstance(transpile(of.QubitOperator("X0"), "cudaq_spin"), cudaq.SpinOperator)

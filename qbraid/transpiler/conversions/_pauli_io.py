# Copyright 2025 qBraid
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
One reader and one writer per library for the Pauli-operator conversions.

Every ``<a>_to_<b>`` conversion is ``write_b(read_a(op))``, so each library's
conventions (qubit order, width, coefficient types) are handled in exactly one
place, and a conversion needs only its own two libraries installed.

"""
# pylint: disable=import-outside-toplevel
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.conversions._pauli_terms import (
    OperatorConversionError,
    PauliTerms,
    coefficient,
    qubit_index,
    width,
)

if TYPE_CHECKING:
    import braket.circuits.observable
    import cirq
    import cudaq
    import openfermion
    import pennylane
    from qiskit.quantum_info import SparsePauliOp


def read_qiskit_pauli(op: SparsePauliOp) -> PauliTerms:
    """Qiskit labels are little-endian: the rightmost character is qubit 0."""
    terms = []
    for label, coeff in zip(op.paulis.to_labels(), op.coeffs):
        n = len(label)
        terms.append(({n - 1 - i: p for i, p in enumerate(label) if p != "I"}, coefficient(coeff)))
    return PauliTerms(terms, op.num_qubits)


def write_qiskit_pauli(operator: PauliTerms) -> SparsePauliOp:
    """Width is the source's if it recorded one, else one past the highest qubit (min. 1)."""
    from qiskit.quantum_info import SparsePauliOp

    n = max(width(operator.terms, operator.declared_width), 1)
    return SparsePauliOp.from_sparse_list(
        [("".join(p.values()), list(p), c) for p, c in operator.terms], num_qubits=n
    )


def read_openfermion_qubit(op: openfermion.QubitOperator) -> PauliTerms:
    """OpenFermion keys terms by ``(index, pauli)`` pairs and records no width."""
    return PauliTerms(
        [({qubit_index(q): p for q, p in term}, coefficient(c)) for term, c in op.terms.items()]
    )


def write_openfermion_qubit(operator: PauliTerms) -> openfermion.QubitOperator:
    """Trailing identity qubits are not representable and are dropped."""
    from openfermion import QubitOperator

    result = QubitOperator()
    for paulis, coeff in operator.terms:
        result += QubitOperator(tuple(sorted(paulis.items())), coeff)
    return result


def read_cirq_pauli(op: cirq.PauliSum) -> PauliTerms:
    """``LineQubit(i)`` is qubit ``i``; other qubit types have no unambiguous index."""
    import cirq

    def index(qubit):
        return qubit_index(qubit.x if isinstance(qubit, cirq.LineQubit) else qubit)

    return PauliTerms(
        [
            ({index(q): str(p) for q, p in string.items()}, coefficient(string.coefficient))
            for string in op
        ]
    )


def write_cirq_pauli(operator: PauliTerms) -> cirq.PauliSum:
    """Writes onto ``LineQubit`` s; trailing identity qubits are dropped."""
    import cirq

    pauli = {"X": cirq.X, "Y": cirq.Y, "Z": cirq.Z}
    return cirq.PauliSum.from_pauli_strings(
        [
            cirq.PauliString(
                {cirq.LineQubit(i): pauli[p] for i, p in paulis.items()}, coefficient=c
            )
            for paulis, c in operator.terms
        ]
    )


def read_pennylane_pauli(op: pennylane.pauli.PauliSentence) -> PauliTerms:
    """Wires must be integers; string or other wire labels have no unambiguous index."""
    return PauliTerms(
        [({qubit_index(w): p for w, p in word.items()}, coefficient(c)) for word, c in op.items()]
    )


def write_pennylane_pauli(operator: PauliTerms) -> pennylane.pauli.PauliSentence:
    """Writes onto integer wires; trailing identity qubits are dropped."""
    from pennylane.pauli import PauliSentence, PauliWord

    sentence = PauliSentence()
    for paulis, coeff in operator.terms:
        word = PauliWord(paulis)
        sentence[word] = sentence.get(word, 0) + coeff
    return sentence


def read_braket_observable(op: braket.circuits.observable.Observable) -> PauliTerms:
    """Every factor must carry its qubit (``X(0) @ Z(1)``); an untargeted observable
    (``X() @ Z()``) has no positions until a result type supplies them."""
    from braket.circuits.observables import I, Sum, TensorProduct, X, Y, Z

    def pauli_name(factor) -> str:
        for kind, name in ((X, "X"), (Y, "Y"), (Z, "Z"), (I, "I")):
            if isinstance(factor, kind):
                return name
        raise OperatorConversionError(
            f"Braket observable {type(factor).__name__} is not a Pauli operator."
        )

    terms = []
    for summand in op.summands if isinstance(op, Sum) else [op]:
        factors = summand.factors if isinstance(summand, TensorProduct) else [summand]
        paulis: dict[int, str] = {}
        for factor in factors:
            name = pauli_name(factor)
            if not factor.targets:
                raise OperatorConversionError(
                    "Braket observable has no qubit targets. Build it with targets, e.g. "
                    "X(0) @ Z(1), so each factor names its qubit."
                )
            if name != "I":
                paulis[qubit_index(int(factor.targets[0]))] = name
        terms.append((paulis, coefficient(op.coefficient) * coefficient(summand.coefficient)))
    return PauliTerms(terms)


def write_braket_observable(operator: PauliTerms) -> braket.circuits.observable.Observable:
    """Writes targeted observables. Braket has no empty sum, and every factor needs a
    qubit, so an identity term or the zero operator is written on qubit 0."""
    from braket.circuits.observables import I, Sum, TensorProduct, X, Y, Z

    pauli = {"X": X, "Y": Y, "Z": Z}
    summands = []
    for paulis, coeff in operator.terms:
        factors = [pauli[p](q) for q, p in sorted(paulis.items())] or [I(0)]
        term = factors[0] if len(factors) == 1 else TensorProduct(factors)
        summands.append(coeff * term)
    if not summands:
        return 0 * I(0)
    return summands[0] if len(summands) == 1 else Sum(summands)


def read_cudaq_spin(op: cudaq.SpinOperator) -> PauliTerms:
    """CUDA-Q's ``qubit_count`` counts qubits acted on, not width, so no width is recorded.
    Identity factors (``I3``) carry an index but act as identity and are dropped."""
    terms = []
    for term in op:
        if not term.coefficient.is_constant():
            raise OperatorConversionError(
                f"Only numeric coefficients can be converted; term {term} has a parameterised "
                "coefficient. Bind parameters before converting."
            )
        paulis = {
            qubit_index(element.target): str(element.as_pauli()).rsplit(".", 1)[-1]
            for element in term
        }
        terms.append(
            (
                {q: p for q, p in paulis.items() if p != "I"},
                coefficient(term.evaluate_coefficient()),
            )
        )
    return PauliTerms(terms)


def write_cudaq_spin(operator: PauliTerms) -> cudaq.SpinOperator:
    """Always returns a ``SpinOperator``, even for one term, so the result keeps its alias."""
    import cudaq
    from cudaq import spin

    # pybind members pylint cannot see.
    pauli = {"X": spin.x, "Y": spin.y, "Z": spin.z}  # pylint: disable=no-member
    result = cudaq.SpinOperator.empty()
    for paulis, coeff in operator.terms:
        term = cudaq.SpinOperator.identity()
        for q, p in sorted(paulis.items()):
            term = term * pauli[p](q)
        result = result + coeff * term
    return result

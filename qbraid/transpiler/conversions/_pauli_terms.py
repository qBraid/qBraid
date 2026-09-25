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
Library-neutral Pauli terms shared by the operator conversions.

Every operator conversion goes through this form: a list of ``(paulis, coefficient)``
where ``paulis`` maps an integer qubit index to ``"X"``, ``"Y"`` or ``"Z"``, plus the
operator's width when the source library records one. Qubit ``i`` is the same physical
qubit in every library; only the libraries' own label conventions differ.

"""
from __future__ import annotations

import numbers
from typing import Any, NamedTuple

PauliTerm = tuple[dict[int, str], complex]


class PauliTerms(NamedTuple):
    """An operator's terms, plus its width when the source library records one."""

    terms: list[PauliTerm]
    declared_width: int | None = None


class OperatorConversionError(ValueError):
    """An operator cannot be converted without guessing at its meaning."""


def coefficient(value: Any) -> complex:
    """Return ``value`` as a complex number, refusing symbolic coefficients."""
    if isinstance(value, numbers.Number):
        return complex(value)
    raise OperatorConversionError(
        f"Only numeric coefficients can be converted; got {type(value).__name__} "
        f"({value!r}). Bind parameters before converting."
    )


def qubit_index(qubit: Any) -> int:
    """Return an integer qubit index, refusing labels that have no unambiguous one."""
    if isinstance(qubit, bool) or not isinstance(qubit, numbers.Integral) or qubit < 0:
        raise OperatorConversionError(
            f"Qubit label {qubit!r} is not a non-negative integer, so it has no "
            "unambiguous position in the target library."
        )
    return int(qubit)


def width(terms: list[PauliTerm], declared: int | None = None) -> int:
    """Operator width: the declared width if known, else one past the largest index."""
    used = max((max(paulis) + 1 for paulis, _ in terms if paulis), default=0)
    if declared is None:
        return used
    if declared < used:
        raise OperatorConversionError(f"Declared width {declared} < highest qubit used {used}.")
    return declared

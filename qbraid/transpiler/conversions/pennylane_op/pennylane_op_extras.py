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
Module defining conversions between PennyLane operators and ``PauliSentence``.

"""
# pylint: disable=import-outside-toplevel
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.conversions._pauli_terms import OperatorConversionError

if TYPE_CHECKING:
    import pennylane

__all__ = ["pennylane_op_to_pennylane_pauli"]


@weight(1)
def pennylane_op_to_pennylane_pauli(
    op: pennylane.operation.Operator,
) -> pennylane.pauli.PauliSentence:
    """Expand a PennyLane operator (``qml.X(0) @ qml.Z(1) + ...``) into a ``PauliSentence``.

    Operators with no Pauli representation (e.g. a parametrised rotation gate) are refused.
    """
    sentence = op.pauli_rep
    if sentence is None:
        raise OperatorConversionError(
            f"{type(op).__name__} has no Pauli representation, so it is not a Pauli operator."
        )
    return sentence

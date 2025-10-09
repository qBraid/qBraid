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
Module containing functions to convert from pyQuil's circuit
representation (Quil programs) to Cirq's circuit representation.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError

from .cirq_quil_input import circuit_from_quil

if TYPE_CHECKING:
    import cirq.circuits
    import pyquil.quil


@weight(1)
def pyquil_to_cirq(program: pyquil.quil.Program) -> cirq.circuits.Circuit:
    """Returns a Cirq circuit equivalent to the input pyQuil Program.

    Args:
        program: PyQuil Program to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input pyQuil Program.
    """
    try:
        return circuit_from_quil(program.out())
    except Exception as err:
        raise ProgramConversionError(
            "qBraid transpiler doesn't yet support pyQuil noise gates."
        ) from err

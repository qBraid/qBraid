# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing functions to convert from pyQuil's circuit
representation (Quil programs) to Cirq's circuit representation.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import CircuitConversionError

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
        raise CircuitConversionError(
            "qBraid transpiler doesn't yet support pyQuil noise gates."
        ) from err

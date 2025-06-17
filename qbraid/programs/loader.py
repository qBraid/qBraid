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
Module containing top-level qbraid program loader functionality
utilizing entrypoints via ``importlib``.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Union

import openqasm3

from qbraid._entrypoints import load_entrypoint
from qbraid.exceptions import QbraidError

from .alias_manager import get_program_type_alias
from .exceptions import ProgramLoaderError
from .registry import QPROGRAM

if TYPE_CHECKING:
    from qbraid.programs.ahs import AnalogHamiltonianProgram
    from qbraid.programs.annealing import AnnealingProgram
    from qbraid.programs.gate_model import GateModelProgram


def load_program(
    program: QPROGRAM,
) -> Union[GateModelProgram, AnalogHamiltonianProgram, AnnealingProgram]:
    """Apply qbraid quantum program wrapper to a supported quantum program.

    This function is used to create a qBraid :class:`~qbraid.programs.QuantumProgram`
    object, which can then be transpiled to any supported quantum circuit-building package.
    The input quantum circuit object must be an instance of a circuit object derived from a
    supported package.

    Args:
        program: A supported quantum circuit/program object.

    Returns:
        QuantumProgram: A wrapped quantum program object of the inferred subclass.

    Raises:
        :class:`~qbraid.ProgramLoaderError`: If the input circuit is not a supported quantum program

    """
    if isinstance(program, openqasm3.ast.Program):
        program = openqasm3.dumps(program)

    try:
        package = get_program_type_alias(program)
    except QbraidError as err:
        raise ProgramLoaderError(f"Error loading quantum program of type {type(program)}") from err

    try:
        load_program_class = load_entrypoint("programs", package)
    except Exception as err:
        raise ProgramLoaderError(f"Error loading quantum program of type {type(program)}") from err

    program_instance = load_program_class(program)

    return program_instance

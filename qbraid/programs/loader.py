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
utilizing entrypoints via ``importlib`` for Python >= 3.10 or
``pkg_resources`` for Python 3.9.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import openqasm3

from qbraid._entrypoints import load_entrypoint
from qbraid.exceptions import QbraidError

from .alias_manager import get_program_type_alias

if TYPE_CHECKING:
    import qbraid.programs


class ProgramLoaderError(QbraidError):
    """Raised when an error occurs while loading a quantum program."""


def load_program(program: Any) -> qbraid.programs.QuantumProgram:
    """Apply qbraid quantum program wrapper to a supported quantum program.

    This function is used to create a qBraid :class:`~qbraid.programs.QuantumProgram`
    object, which can then be transpiled to any supported quantum circuit-building package.
    The input quantum circuit object must be an instance of a circuit object derived from a
    supported package.

    Args:
        circuit (:data:`~qbraid.programs.QPROGRAM`): A supported quantum circuit / program object

    Returns:
        :class:`~qbraid.programs.QuantumProgram`: A wrapped quantum circuit-like object

    Raises:
        :class:`~qbraid.QbraidError`: If the input circuit is not a supported quantum program.

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

    return load_program_class(program)

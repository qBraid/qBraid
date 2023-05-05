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
Module for drawing quantum circuit diagrams

"""
from typing import TYPE_CHECKING

from qbraid.exceptions import ProgramTypeError

if TYPE_CHECKING:
    import qbraid


def draw(program: "qbraid.QPROGRAM") -> None:
    """Draws circuit diagram.

    Args:
        :data:`~.qbraid.QPROGRAM`: Supported quantum program

    Raises:
        ProgramTypeError: If quantum program is not of a supported type
    """
    # todo: visualization from supportive framework
    try:
        package = program.__module__
    except AttributeError as err:
        raise ProgramTypeError(program) from err

    if "qiskit" in package:
        print(program.draw())

    elif "braket" in package or "cirq" in package or "pyquil" in package:
        print(program)

    else:
        raise ProgramTypeError(program)

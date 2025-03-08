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
Module for drawing quantum circuit diagrams
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import qbraid.programs


def circuit_drawer(program: qbraid.programs.QPROGRAM, **kwargs) -> Any:
    """Draws circuit diagram by calling the program's native draw method.

    Args:
        program: A qBraid GateModelProgram or subclass instance.

    Returns:
        The result of the program's draw method (e.g., a figure, ASCII text, etc.).
    """
    # Simply delegate to the program's draw method
    return program.draw(**kwargs)

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
Module containing OpenQASM 3 conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

qbraid_qir = LazyLoader("qbraid_qir", globals(), "qbraid_qir")

if TYPE_CHECKING:
    import pyqir

    from qbraid.programs.typer import Qasm3StringType


@requires_extras("qbraid_qir")
def qasm3_to_pyqir(program: Qasm3StringType) -> pyqir.Module:
    """Returns a PyQIR module equivalent to the input OpenQASM 3 program.

    Args:
        program (str): OpenQASM 3 program circuit to convert to PyQIR module.

    Returns:
        pyqir.Module: module equivalent to input OpenQASM 3 program.
    """
    return qbraid_qir.qasm3.qasm3_to_qir(program)

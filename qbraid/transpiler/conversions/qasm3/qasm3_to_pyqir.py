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
Module containing OpenQASM 3 to QIR conversion function

"""

from typing import TYPE_CHECKING

from qbraid._import import LazyLoader
from qbraid.transpiler.annotations import requires_extras

qbraid_qir = LazyLoader("qbraid_qir", globals(), "qbraid_qir")

if TYPE_CHECKING:
    import pyqir


@requires_extras("qbraid_qir.qasm3")
def qasm3_to_qir(qasm3: str) -> "pyqir.Module":
    """Convert QASM 3.0 string to a QIR Program representation.

    Args:
        qasm3 (str): A string in QASM 3.0 format.

    Returns:
        qbraid_qir.Program: A Program object representing the input QASM 3.0 string.
    """
    return qbraid_qir.qasm3.qasm3_to_qir(qasm3)

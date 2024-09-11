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
Module containing functions to convert between OpenQASM 2 and PyTKET.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight

pytket_qasm = LazyLoader("pytket_qasm", globals(), "pytket.qasm")

if TYPE_CHECKING:
    import pytket.circuit

    from qbraid.programs.typer import Qasm2StringType


@weight(1)
def qasm2_to_pytket(qasm: Qasm2StringType) -> pytket.circuit.Circuit:
    """Returns a pytket circuit equivalent to the input OpenQASM 2 string.

    Args:
        qasm (str): OpenQASM 2 string to convert to a pytket circuit.

    Returns:
        pytket.circuit.Circuit: PyTKET circuit object equivalent to input OpenQASM 2 string.
    """
    return pytket_qasm.circuit_from_qasm_str(qasm)

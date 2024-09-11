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

from pytket.qasm import circuit_to_qasm_str

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    import pytket.circuit

    from qbraid.programs.typer import Qasm2StringType


@weight(1)
def pytket_to_qasm2(circuit: pytket.circuit.Circuit) -> Qasm2StringType:
    """Returns an OpenQASM 2 string equivalent to the input pytket circuit.

    Args:
        circuit (pytket.circuit.Circuit): PyTKET circuit to convert to OpenQASM 2 string.

    Returns:
        str: OpenQASM 2 string equivalent to input pytket circuit.
    """
    return circuit_to_qasm_str(circuit)

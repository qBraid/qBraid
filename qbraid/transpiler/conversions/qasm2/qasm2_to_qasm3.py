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
Module containing OpenQASM conversion function

"""
import pyqasm

from qbraid.programs.typer import Qasm2String, Qasm2StringType, Qasm3StringType
from qbraid.transpiler.annotations import weight


@weight(0.7)
def qasm2_to_qasm3(qasm_str: Qasm2StringType) -> Qasm3StringType:
    """Convert a OpenQASM 2.0 string to OpenQASM 3.0 string

    Args:
        qasm_str (str): OpenQASM 2.0 string

    Returns:
        str: OpenQASM 3.0 string
    """
    if not isinstance(qasm_str, Qasm2String):
        raise ValueError("Invalid OpenQASM 2.0 string")

    qasm_module = pyqasm.loads(qasm_str)
    return qasm_module.to_qasm3(as_str=True)

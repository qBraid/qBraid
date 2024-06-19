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
import openqasm3

from qbraid.transpiler.annotations import weight


@weight(1)
def openqasm3_to_qasm3(program: openqasm3.ast.Program) -> str:
    """Dumps openqasm3.ast.Program to an OpenQASM 3.0 string

    Args:
        program (openqasm3.ast.Program): OpenQASM 3.0 AST program

    Returns:
        str: OpenQASM 3.0 string
    """
    return openqasm3.dumps(program)

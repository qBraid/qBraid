# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=invalid-name


"""
Module defining OpenQasm3Program Class

"""
import openqasm3

from qbraid.programs.qasm3 import Qasm3Program


class OpenQasmAstProgram(Qasm3Program):
    """Wrapper class for OpenqasmAstProgram objects."""

    def __init__(self, qasm_ast: openqasm3.ast.Program):
        """Create a OpenqasmAstProgram object.

        Args:
            circuit: the OpenQASM Ast object to be wrapped

        """
        # coverage: ignore
        super().__init__(openqasm3.dumps(qasm_ast))

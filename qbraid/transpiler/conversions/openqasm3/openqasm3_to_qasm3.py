# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module containing OpenQASM to QASM 3 conversion function

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import openqasm3

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    from qbraid.programs.typer import Qasm3StringType


@weight(1)
def openqasm3_to_qasm3(program: openqasm3.ast.Program) -> Qasm3StringType:
    """Dumps openqasm3.ast.Program to an OpenQASM 3.0 string

    Args:
        program (openqasm3.ast.Program): OpenQASM 3.0 AST program

    Returns:
        str: OpenQASM 3.0 string
    """
    statements = program.statements
    program = openqasm3.ast.Program(statements=statements, version="3.0")
    return openqasm3.dumps(program)

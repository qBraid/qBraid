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
Module defining OpenQASM 2 to pyQuil conversion function.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.conversions.openqasm3.openqasm3_to_pyquil import openqasm3_to_pyquil

if TYPE_CHECKING:
    from pyquil import Program

    from qbraid.programs.typer import Qasm2StringType


@weight(1.0)
def qasm2_to_pyquil(qasm: Qasm2StringType) -> Program:
    """Returns a pyQuil Program equivalent to the input OpenQASM 2 program.

    OpenQASM 2 is a subset of OpenQASM 3 for the purposes of this conversion, so
    the OpenQASM 3 converter is reused directly. Routing through it (rather than
    through Cirq, which was previously the shortest path in the conversion graph)
    preserves two properties that Rigetti's ProtoQuil dialect requires and that a
    Cirq round trip does not keep:

    * Instruction order. A ``cirq.Circuit`` stores operations in moments, so
      rebuilding a program from it emits each measurement as early as it can be
      scheduled, interleaving measurements with gates on other qubits.
    * A single classical register. Cirq's Quil writer declares one ``BIT[1]``
      register per measurement key (``m0``, ``m1``, ...), losing the source
      register layout, whereas this emits one ``ro`` register whose bit indices
      are the declared ``creg`` bit indices.

    Args:
        qasm (str): OpenQASM 2 program to convert.

    Returns:
        pyquil.Program: pyQuil Program equivalent to the input program.

    Raises:
        ProgramConversionError: If the program is malformed or contains a
            gate/statement that is not supported by the conversion.
    """
    return openqasm3_to_pyquil(qasm)

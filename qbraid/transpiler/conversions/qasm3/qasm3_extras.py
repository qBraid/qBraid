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
Module containing OpenQASM 3 conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.passes.qasm.compat import add_stdgates_include, insert_gate_def, replace_gate_names
from qbraid.transpiler.annotations import requires_extras

qbraid_qir = LazyLoader("qbraid_qir", globals(), "qbraid_qir")
autoqasm = LazyLoader("autoqasm", globals(), "autoqasm")

if TYPE_CHECKING:
    import autoqasm as aq

aq_to_qasm3_stdgates = {
    "ccnot": "ccx",
    "cnot": "cx",
    "cphaseshift": "cp",
    "i": "id",
    "phaseshift": "p",
    "si": "sdg",
    "ti": "tdg",
    "v": "sx",
    "vi": "sxdg",
}


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


@requires_extras("autoqasm")
def autoqasm_to_qasm3(program: aq.program.program.Program) -> Qasm3StringType:
    """Converts an AutoQASM program to an OpenQASM 3 program of gates from the
    Standard Gate Library. The program must be built prior to conversion using
    the .build() method.

    Args:
        program (autoqasm.program.program.Program): AutoQASM program to convert
            to OpenQASM 3.

    Returns:
        str: OpenQASM 3 program equivalent to input AutoQASM program.
    """
    qasm = program.to_ir()
    # Convert to Standard Library qasm3 gates
    qasm = replace_gate_names(qasm, aq_to_qasm3_stdgates)
    # Insert custom gate conversions
    qasm = insert_gate_def(qasm, ["iswap", "sxdg", "cv"])
    # AutoQASM does not include stdgates.inc
    qasm = add_stdgates_include(qasm)
    return qasm

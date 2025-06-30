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

from qbraid.passes.qasm.compat import add_stdgates_include, insert_gate_def, replace_gate_names
from qbraid.transpiler.annotations import requires_extras

qbraid_qir = LazyLoader("qbraid_qir", globals(), "qbraid_qir")
autoqasm = LazyLoader("autoqasm", globals(), "autoqasm")

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
def autoqasm_to_qasm3(program: autoqasm.program.program.Program) -> Qasm3StringType:
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
    for aq_gate, qasm3_gate in aq_to_qasm3_stdgates.items():
        qasm = replace_gate_names(qasm, {aq_gate: qasm3_gate})

    # Insert custom gate conversions
    qasm = insert_gate_def(qasm, "iswap")
    qasm = insert_gate_def(qasm, "sxdg")
    qasm = insert_gate_def(qasm, "cv")
    # AutoQASM does not include stdgates.inc
    qasm = add_stdgates_include(qasm)
    return qasm



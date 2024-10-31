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
Module for converting Braket circuits to/from OpenQASM 3

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.passes.qasm.compat import (
    convert_qasm_pi_to_decimal,
    remove_stdgates_include,
    replace_gate_name,
)
from qbraid.programs.exceptions import QasmError
from qbraid.transpiler.annotations import weight

braket_circuits = LazyLoader("braket_circuits", globals(), "braket.circuits")
braket_openqasm = LazyLoader("braket_openqasm", globals(), "braket.ir.openqasm")

if TYPE_CHECKING:
    import braket.circuits

    from qbraid.programs.typer import Qasm3StringType


def transform_notation(qasm3: str) -> str:
    """
    Process an OpenQASM 3 program that was generated by
    an external tool to make it compatible with Amazon Braket.

    """
    replacements = {
        "cx": "cnot",
        "sdg": "si",
        "tdg": "ti",
        "sx": "v",
        "sxdg": "vi",
        "p": "phaseshift",
        "cp": "cphaseshift",
    }

    qasm3 = remove_stdgates_include(qasm3)
    for old, new in replacements.items():
        qasm3 = replace_gate_name(qasm3, old, new)
    qasm3 = convert_qasm_pi_to_decimal(qasm3)
    return qasm3


@weight(1)
def qasm3_to_braket(qasm: Qasm3StringType) -> braket.circuits.Circuit:
    """Converts an OpenQASM 3.0 string to a ``braket.circuits.Circuit``.

    Args:
        qasm: OpenQASM 3 string

    Returns:
        The Amazon Braket circuit equivalent to the input OpenQASM 3.0 string

    Raises:
        ProgramConversionError: If qasm to braket conversion fails

    """
    qasm = transform_notation(qasm)

    try:
        program = braket_openqasm.Program(source=qasm)
        return braket_circuits.Circuit.from_ir(source=program.source, inputs=program.inputs)
    except Exception as err:
        raise QasmError("Error converting qasm3 string to braket circuit") from err

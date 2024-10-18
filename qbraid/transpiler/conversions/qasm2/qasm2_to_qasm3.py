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
import os
import textwrap

from qbraid._version import __version__ as qbraid_version
from qbraid.passes.qasm.decompose import _decompose_rxx_instr
from qbraid.passes.qasm.format import remove_unused_gates
from qbraid.programs.typer import Qasm2String, Qasm2StringType, Qasm3StringType
from qbraid.transpiler.annotations import weight


def _get_qasm3_gate_defs() -> str:
    """Helper function to get openqasm 3 gate defs from .qasm file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    qelib_qasm = os.path.join(current_dir, "qelib_qasm3.qasm")
    with open(qelib_qasm, mode="r", encoding="utf-8") as file:
        gate_defs = file.read()
    return gate_defs


def _build_qasm_3_reg(line: str, qreg_type: bool) -> str:
    """Helper function to build openqasm 3 register statements

    Args:
        line (str): openqasm 2  regdecl statement
        qreg_type (bool): whether a qreg or creg type statement

    Returns:
        str : openqasm 3 qubits / bits declaration
    """
    reg_keyword_len = 4
    line = line[reg_keyword_len:]
    elements = line.split("[")
    reg_name = elements[0].strip()
    reg_size = elements[1].split("]")[0].strip()
    result = "\nqubit" if qreg_type else "bit"
    result += f"[{reg_size}] {reg_name};\n"
    return result


def _build_qasm_3_measure(line: str) -> str:
    """Helper function to build openqasm 3 measure string

    Args:
        line (str): openqasm 2 measure statement

    Returns:
        str:  openqasm 3 measure statement
    """
    measure_keyword_len = 7
    line = line[measure_keyword_len:]
    elements = line.split("->")
    qubits_name = elements[0].replace(" ", "")
    bits_name = elements[1].split(";")[0].replace(" ", "")

    return f"{bits_name} = measure {qubits_name};\n"


def _convert_line_to_qasm3(line: str) -> str:
    """Function to change an openqasm 2 line to openqasm 3

    Args:
        line (str): an openqasm 2 line

    Returns:
        str: corresponding openqasm 3 line
    """
    line = line.lstrip()
    if line.startswith("OPENQASM"):
        return ""
    if "qelib1.inc" in line:
        return ""
    if line.startswith("qreg"):
        return _build_qasm_3_reg(line, qreg_type=True)
    if line.startswith("creg"):
        return _build_qasm_3_reg(line, qreg_type=False)
    if line.startswith("u("):
        return line.replace("u(", "U(")
    if line.startswith("rxx("):
        return _decompose_rxx_instr(line)
    if line.startswith("measure"):
        return _build_qasm_3_measure(line)
    if line.startswith("opaque"):
        # as opaque is ignored by openqasm 3 add it as a comment
        return "// " + line + "\n"
    return line + "\n"


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

    qasm3_str = textwrap.dedent(
        f"""
        // Generated from qBraid v{qbraid_version}
        OPENQASM 3.0;
        include 'stdgates.inc';
    """
    )

    gate_defs = _get_qasm3_gate_defs()

    for line in gate_defs:
        qasm3_str += line

    last_line_was_blank = False

    for line in qasm_str.splitlines():
        if line.strip().startswith("//"):
            continue

        # Check if the current line is blank
        if not line.strip():
            if last_line_was_blank:
                continue  # pragma: no cover

            last_line_was_blank = True
        else:
            last_line_was_blank = False

        line = _convert_line_to_qasm3(line)
        qasm3_str += line

    qasm3_str = remove_unused_gates(qasm3_str)

    return qasm3_str

# Copyright (C) 2023 qBraid
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

import openqasm3

from qbraid.programs.inspector import get_qasm_version
from qbraid.programs.qasm_qelib1 import _decompose_rxx_instr

QASMType = str


def _get_qasm3_gate_defs() -> str:
    """Helper function to get openqasm 3 gate defs from .qasm file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    qelib_qasm = os.path.join(current_dir, "qelib_qasm3.qasm")
    with open(qelib_qasm, mode="r", encoding="utf-8") as file:
        gate_defs = file.read()
    return gate_defs


def _build_qasm_3_reg(line: str, qreg_type: bool) -> QASMType:
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
    result = "qubit" if qreg_type else "bit"
    result += f"[{reg_size}] {reg_name};\n"
    return result


def _build_qasm_3_measure(line: str) -> QASMType:
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


def _convert_line_to_qasm3(line: str) -> QASMType:
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


def qasm2_to_qasm3(qasm_str: str) -> QASMType:
    """Convert a OpenQASM 2.0 string to OpenQASM 3.0 string

    Args:
        qasm_str (str): OpenQASM 2.0 string

    Returns:
        str: OpenQASM 3.0 string
    """
    qasm_version = get_qasm_version(qasm_str)
    if not qasm_version == "qasm2":
        raise ValueError("Invalid OpenQASM 2.0 string")

    qasm3_str = "OPENQASM 3.0;\ninclude 'stdgates.inc';"

    gate_defs = _get_qasm3_gate_defs()

    for line in gate_defs:
        qasm3_str += line

    for line in qasm_str.splitlines():
        line = _convert_line_to_qasm3(line)
        qasm3_str += line

    return qasm3_str


def qasm3_to_openqasm3(qasm_str: str) -> openqasm3.ast.Program:
    """Loads an openqasm3.ast.Program from an OpenQASM 3.0 string

    Args:
        qasm_str (str): OpenQASM 3.0 string

    Returns:
        openqasm3.ast.Program: OpenQASM 3.0 AST program
    """
    return openqasm3.parse(qasm_str)


def openqasm3_to_qasm3(program: openqasm3.ast.Program) -> str:
    """Dumps openqasm3.ast.Program to an OpenQASM 3.0 string

    Args:
        program (openqasm3.ast.Program): OpenQASM 3.0 AST program

    Returns:
        str: OpenQASM 3.0 string
    """
    return openqasm3.dumps(program)

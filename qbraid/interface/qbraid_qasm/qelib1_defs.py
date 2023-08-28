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
Module that implements qelib1.inc qasm gate definitions as python functions

"""
import re
from typing import Optional

from qbraid.exceptions import QasmError


def _get_param(instr: str) -> Optional[str]:
    try:
        return instr[instr.index("(") + 1 : instr.index(")")]
    except ValueError:
        return None


def _remove_spaces_in_parentheses(expression):
    # Find all parenthesized parts of the input.
    parenthesized_parts = re.findall(r"\(.*?\)", expression)

    for part in parenthesized_parts:
        # For each parenthesized part, remove all the spaces.
        cleaned_part = part.replace(" ", "")

        # Replace the original part in the expression with the cleaned part.
        expression = expression.replace(part, cleaned_part)

    return expression


def _decompose_cu_instr(instr: str) -> str:
    """controlled-U gate"""
    try:
        instr = _remove_spaces_in_parentheses(instr)
        cu_gate, qs = instr.split(" ")
        a, b = qs.strip(";").split(",")
        params_lst = _get_param(cu_gate).split(",")
        params = [float(x) for x in params_lst]
        theta, phi, lam, gamma = params
    except (AttributeError, ValueError) as err:
        raise QasmError from err
    instr_out = "\n// cu gate\n"
    instr_out += f"p({gamma}) {a};\n"
    instr_out += f"p({(lam+phi)/2}) {a};\n"
    instr_out += f"p({(lam-phi)/2}) {b};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out += f"u({-1*theta/2},0,{-1*(phi+lam)/2}) {b};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out += f"u({theta/2},{phi},0) {b};\n\n"
    return instr_out


def _decompose_rxx_instr(instr: str) -> str:
    """two-qubit XX rotation"""
    try:
        instr = instr.replace(", ", ",")
        rxx_gate, qs = instr.split(" ")
        a, b = qs.strip(";").split(",")
        theta = _get_param(rxx_gate)
    except (AttributeError, ValueError) as err:
        raise QasmError from err
    instr_out = "\n// rxx gate\n"
    instr_out += f"h {a};\n"
    instr_out += f"h {b};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out += f"rz({theta}) {b};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out += f"h {b};\n"
    instr_out += f"h {a};\n\n"
    return instr_out


def _decompose_rccx_instr(instr: str) -> str:
    """relative-phase CCX"""
    try:
        _, qs = instr.split(" ")
        a, b, c = qs.strip(";").split(",")
    except (AttributeError, ValueError) as err:
        raise QasmError from err
    instr_out = "\n// rccx gate\n"
    instr_out += f"u2(0,pi) {c};\n"
    instr_out += f"u1(pi/4) {c};\n"
    instr_out += f"cx {b},{c};\n"
    instr_out += f"u1(-pi/4) {c};\n"
    instr_out += f"cx {a},{c};\n"
    instr_out += f"u1(pi/4) {c};\n"
    instr_out += f"cx {b},{c};\n"
    instr_out += f"u1(-pi/4) {c};\n"
    instr_out += f"u2(0,pi) {c};\n\n"
    return instr_out


def _decompose_rc3x_instr(instr: str) -> str:
    """relative-phase 3-controlled X gate"""
    try:
        _, qs = instr.split(" ")
        a, b, c, d = qs.strip(";").split(",")
    except (AttributeError, ValueError) as err:
        raise QasmError from err
    instr_out = "\n// rc3x gate\n"
    instr_out += f"u2(0,pi) {d};\n"
    instr_out += f"u1(pi/4) {d};\n"
    instr_out += f"cx {c},{d};\n"
    instr_out += f"u1(-pi/4) {d};\n"
    instr_out += f"u2(0,pi) {d};\n"
    instr_out += f"cx {a},{d};\n"
    instr_out += f"u1(pi/4) {d};\n"
    instr_out += f"cx {b},{d};\n"
    instr_out += f"u1(-pi/4) {d};\n"
    instr_out += f"cx {a},{d};\n"
    instr_out += f"u1(pi/4) {d};\n"
    instr_out += f"cx {b},{d};\n"
    instr_out += f"u1(-pi/4) {d};\n"
    instr_out += f"u2(0,pi) {d};\n"
    instr_out += f"u1(pi/4) {d};\n"
    instr_out += f"cx {c},{d};\n"
    instr_out += f"u1(-pi/4) {d};\n"
    instr_out += f"u2(0,pi) {d};\n\n"
    return instr_out


def replace_qelib1_defs(qasm_str: str) -> str:
    """Replace edge-case qelib1 gates with equivalent decomposition."""
    qasm_lst_out = []
    qasm_lst = qasm_str.split("\n")

    for _, qasm_line in enumerate(qasm_lst):
        line_str = qasm_line
        len_line = len(line_str)
        if len_line > 3 and line_str[0:3] == "cu(":
            line_str_out = _decompose_cu_instr(line_str)
        elif len_line > 4 and line_str[0:4] == "rxx(":
            line_str_out = _decompose_rxx_instr(line_str)
        elif len_line > 4 and line_str[0:4] == "rccx":
            line_str_out = _decompose_rccx_instr(line_str)
        elif len_line > 4 and line_str[0:4] == "rc3x":
            line_str_out = _decompose_rc3x_instr(line_str)
        else:
            line_str_out = line_str

        qasm_lst_out.append(line_str_out)

    qasm_str_def = "\n".join(qasm_lst_out)
    return qasm_str_def

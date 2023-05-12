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
Module for preprocessing qasm string to before it is passed to parser.

"""
import re
from typing import Optional

from qbraid.transpiler.exceptions import QasmError

GATE_DEFS = {
    "rccx": (
        ["q0", "q1", "q2"],
        "u2(0,pi) q2; u1(pi/4) q2; cx q1,q2; u1(-pi/4) q2; "
        "cx q0,q2; u1(pi/4) q2; cx q1,q2; u1(-pi/4) q2; u2(0,pi) q2;",
    )
}


def _get_param(instr: str) -> Optional[str]:
    try:
        return instr[instr.index("(") + 1 : instr.index(")")]
    except ValueError:
        return None


def _decompose_cu_instr(instr: str) -> str:
    try:
        cu_gate, qs = instr.split(" ")
        q0, q1 = qs.strip(";").split(",")
        params_lst = _get_param(cu_gate).split(",")
        params = [float(x) for x in params_lst]
        theta, phi, lam, gamma = params
    except (AttributeError, ValueError) as err:
        raise QasmError from err
    instr_out = "// CUGate\n"
    instr_out = f"p({gamma}) {q0};\n"
    instr_out += f"p({(lam+phi)/2}) {q0};\n"
    instr_out += f"p({(lam-phi)/2}) {q1};\n"
    instr_out += f"cx {q0},{q1};\n"
    instr_out += f"u({-1*theta/2},0,{-1*(phi+lam)/2}) {q1};\n"
    instr_out += f"cx {q0},{q1};\n"
    instr_out += f"u({theta/2},{phi},0) {q1};\n"
    return instr_out


def _decompose_rxx_instr(instr: str) -> str:
    try:
        rxx_gate, qs = instr.split(" ")
        q0, q1 = qs.strip(";").split(",")
        theta = _get_param(rxx_gate)
    except (AttributeError, ValueError) as err:
        raise QasmError from err
    instr_out = "// RXXGate\n"
    instr_out = f"h {q0};\n"
    instr_out += f"h {q1};\n"
    instr_out += f"cx {q0},{q1};\n"
    instr_out += f"rz({theta}) {q1};\n"
    instr_out += f"cx {q0},{q1};\n"
    instr_out += f"h {q1};\n"
    instr_out += f"h {q0};\n"
    return instr_out


def _replace_gate_defs(qasm_line: str, gate_defs: dict) -> str:
    for g in gate_defs:
        instr_lst = qasm_line.split(";")
        instr_lst_out = []
        for instr in instr_lst:
            line_args = instr.split(" ")
            qasm_gate = line_args[0]
            if g != qasm_gate and qasm_gate not in gate_defs:
                param = _get_param(qasm_gate)
                if param is not None:
                    qasm_gate = qasm_gate.replace(param, "param0")
                    if g != qasm_gate:
                        qasm_gate = qasm_gate.replace("param0", "param0,param1")
            if g == qasm_gate:
                qs, instr_def = gate_defs[g]
                map_qs = line_args[1].split(",")
                for i, qs_i in enumerate(qs):
                    instr_def = instr_def.replace(qs_i, map_qs[i])
                instr = instr_def
            if len(instr) > 0:
                instr_lst_out.append(instr)
        instr_lst_out_strip = [x.strip() for x in instr_lst_out]
        qasm_line = ";".join(instr_lst_out_strip) + ";"
        qasm_line = qasm_line.replace(";;", ";")
    return qasm_line


def _remove_barriers(qasm_str: str) -> str:
    """Returns a copy of the input QASM with all barriers removed.

    Args:
        qasm_str: QASM to remove barriers from.
    """
    quoted_re = r"(?:\"[^\"]*?\")"
    # Statements separated by semicolons
    statement_re = r"((?:[^;{}\"]*?" + quoted_re + r"?)*[;{}])?"
    # Comments begin with a pair of forward slashes and end with a new line
    comment_re = r"(\n?//[^\n]*(?:\n|$))?"
    statements_comments = re.findall(statement_re + comment_re, qasm_str)
    lines = []
    # Language is case sensitive. Whitespace is ignored
    for statement, comment in statements_comments:
        if re.match(r"^\s*barrier(?:(?:\s+)|(?:;))", statement) is None:
            lines.append(statement + comment)
    return "".join(lines)


def convert_to_supported_qasm(qasm_str: str) -> str:
    """Returns a copy of the input QASM compatible with the
    :class:`~qbraid.transpiler.cirq_qasm.qasm_parser.QasmParser`.
    Conversion includes deconstruction of custom defined gates, and
    decomposition of unsupported gates/operations.
    
    TODO: Breaks for qiskit>=0.43.0. Updates to helper functions
    and support for new gates needed for latest qiskit version.
    
    """
    gate_defs = GATE_DEFS
    qasm_lst_out = []
    qasm_str = _remove_barriers(qasm_str)
    qasm_lst = qasm_str.split("\n")

    for _, qasm_line in enumerate(qasm_lst):
        line_str = qasm_line
        len_line = len(line_str)
        line_args = line_str.split(" ")
        # add custom gates to gate_defs dict
        if line_args[0] == "gate":
            gate = line_args[1]
            qs = line_args[2].split(",")
            instr = line_str.split("{")[1].strip("}").strip()
            gate_defs[gate] = (qs, instr)
            param_var = _get_param(gate)
            param_def = _get_param(instr)
            if all(v is not None for v in [param_var, param_def]):
                match_gate = gate.replace(param_var, param_def)
                gate_defs[match_gate] = (qs, instr)
            line_str_out = "// " + line_str
        # decompose cu gate into supported gates
        elif len_line > 3 and line_str[0:3] == "cu(":
            line_str_out = _decompose_cu_instr(line_str)
        # decompose rxx gate into supported gates
        elif len_line > 4 and line_str[0:4] == "rxx(":
            line_str_out = _decompose_rxx_instr(line_str)
        # swap out instructions for gates found in gate_defs
        elif line_args[0] in gate_defs:
            qs, instr = gate_defs[line_args[0]]
            map_qs = line_args[1].strip(";").split(",")
            for i, qs_i in enumerate(qs):
                instr = instr.replace(qs_i, map_qs[i])
            line_str_out = instr
        else:
            line_str_out = line_str
        # find and replace any remaining instructions matching gates_defs.
        # Necessary bc initial swap does not recurse for gates defined in
        # terms of other gate(s) in gate_defs.
        if line_str_out[0:2] != "//" and len(line_str_out) > 0:
            line_str_out = _replace_gate_defs(line_str_out, gate_defs)

        qasm_lst_out.append(line_str_out)

    qasm_str_def = "\n".join(qasm_lst_out)
    return qasm_str_def

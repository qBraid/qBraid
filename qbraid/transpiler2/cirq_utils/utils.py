import re
import cirq

QASMType = str

def _remove_qasm_barriers(qasm: QASMType) -> QASMType:
    """Returns a copy of the input QASM with all barriers removed.

    Args:
        qasm: QASM to remove barriers from.

    Note:
        According to the OpenQASM 2.X language specification
        (https://arxiv.org/pdf/1707.03429v2.pdf), "Statements are separated by
        semicolons. Whitespace is ignored. The language is case sensitive.
        Comments begin with a pair of forward slashes and end with a new line."
    """
    quoted_re = r"(?:\"[^\"]*?\")"
    statement_re = r"((?:[^;{}\"]*?" + quoted_re + r"?)*[;{}])?"
    comment_re = r"(\n?//[^\n]*(?:\n|$))?"
    statements_comments = re.findall(statement_re + comment_re, qasm)
    lines = []
    for statement, comment in statements_comments:
        if re.match(r"^\s*barrier(?:(?:\s+)|(?:;))", statement) is None:
            lines.append(statement + comment)
    return "".join(lines)

def _map_qasm_str_to_def(qasm_str):
    gate_defs = {}
    qasm_lst = qasm_str.split("\n")
    qasm_lst_out = []
    for i in range(len(qasm_lst)):
        line_str = qasm_lst[i]
        line_args = line_str.split(" ")
        if line_args[0] == "gate":
            gate = line_args[1]
            qs = line_args[2].split(",")
            instr = line_str.split("{")[1].strip("}").strip()
            gate_defs[gate] = (qs, instr)
            line_str_out = "// " + line_str
        elif line_args[0] in gate_defs:
            qs, instr = gate_defs[line_args[0]]
            map_qs = line_args[1].strip(";").split(",")
            for i in range(len(qs)):
                instr = instr.replace(qs[i], map_qs[i])
            line_str_out = instr
        else:
            line_str_out = line_str
        qasm_lst_out.append(line_str_out)
    return "\n".join(qasm_lst_out)
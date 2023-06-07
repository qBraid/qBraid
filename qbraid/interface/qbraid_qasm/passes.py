# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
import re
from typing import Optional

from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit

from qbraid.interface import circuits_allclose
from qbraid.interface.qbraid_cirq.tools import _convert_to_line_qubits
from qbraid.transpiler.cirq_qasm.qasm_parser import QasmParser
from qbraid.transpiler.exceptions import QasmError


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


def _get_param(instr: str) -> Optional[str]:
    try:
        return instr[instr.index("(") + 1 : instr.index(")")]
    except ValueError:
        return None


def remove_spaces_in_parentheses(expression):
    # Find all parenthesized parts of the input.
    parenthesized_parts = re.findall(r'\(.*?\)', expression)

    for part in parenthesized_parts:
        # For each parenthesized part, remove all the spaces.
        cleaned_part = part.replace(' ', '')

        # Replace the original part in the expression with the cleaned part.
        expression = expression.replace(part, cleaned_part)

    return expression


def _decompose_cu_instr(instr: str) -> str:
    try:
        instr = remove_spaces_in_parentheses(instr)
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


def _decompose_rccx_instr(instr: str) -> str:
    try:
        _, qs = instr.split(" ")
        a, b, c = qs.strip(";").split(",")
    except (AttributeError, ValueError) as err:
        raise QasmError from err
    instr_out = "// relative-phase CCX\n"
    instr_out = f"u2(0,pi) {c};\n"
    instr_out += f"u1(pi/4) {c};\n"
    instr_out += f"cx {b},{c};\n"
    instr_out += f"u1(-pi/4) {c};\n"
    instr_out += f"cx {a},{c};\n"
    instr_out += f"u1(pi/4) {c};\n"
    instr_out += f"cx {b},{c};\n"
    instr_out += f"u1(-pi/4) {c};\n"
    instr_out += f"u2(0,pi) {c};\n"
    return instr_out


def _decompose_c3sqrtx_instr(instr: str) -> str:
    try:
        _, qs = instr.split(" ")
        a, b, c, d = qs.strip(";").split(",")
    except (AttributeError, ValueError) as err:
        raise QasmError from err
    instr_out = "// 3-controlled sqrt(X) gate\n"
    instr_out = f"h {d}; cu1(pi/8) {a},{d}; h {d};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out = f"h {d}; cu1(-pi/8) {b},{d}; h {d};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out = f"h {d}; cu1(pi/8) {b},{d}; h {d};\n"
    instr_out += f"cx {b},{c};\n"
    instr_out = f"h {d}; cu1(-pi/8) {c},{d}; h {d};\n"
    instr_out += f"cx {a},{c};\n"
    instr_out = f"h {d}; cu1(pi/8) {c},{d}; h {d};\n"
    instr_out += f"cx {b},{c};\n"
    instr_out = f"h {d}; cu1(-pi/8) {c},{d}; h {d};\n"
    instr_out += f"cx {a},{c};\n"
    instr_out = f"h {d}; cu1(pi/8) {c},{d}; h {d};\n"
    return instr_out


def _format_qasm_string(qasm_string, skip_pattern):
    lines = qasm_string.split("\n")
    formatted_lines = []

    for line in lines:
        line = line.strip()  # Strip leading and trailing whitespace
        if skip_pattern.match(line) or line.startswith("//"):
            # If the line matches the gate definition pattern, add it as is
            formatted_lines.append(line)
        else:
            # Otherwise, split it at semicolons and add each part as a separate line
            parts = re.split(";[ ]*", line)
            parts = [part + ";" for part in parts if part]  # Remove empty parts
            formatted_lines.extend(parts)

    return "\n".join(formatted_lines)


def _convert_gate_defs(qasm_string):
    # Define regular expression patterns
    gate_definition_pattern = re.compile(
        r"gate ([a-zA-Z0-9_]+)(\((.*?)\))? ((q[0-9]+,)*q[0-9]+) {(.*?)}"
    )

    gate_usage_match = None

    # Find gate definition and extract its components
    gate_definition_match = gate_definition_pattern.search(qasm_string)
    if gate_definition_match:
        gate_name, _, params, qubits, _, gate_body = gate_definition_match.groups()
        params_list = [param.strip() for param in params.split(",")] if params is not None else []

        qubits = [qubit.strip() for qubit in qubits.split(",")]

        # pylint: disable=consider-using-f-string
        gate_usage_pattern = re.compile(
            r"({})(\((.*?)\))? ((q\[([0-9]+)\],)*(q\[([0-9]+)\]));".format(gate_name)
        )

        # Replace parameters with their values in gate body
        gate_usage_match = gate_usage_pattern.search(qasm_string)

    while gate_usage_match:
        groups = gate_usage_match.groups()
        param_values, qubits_usage = groups[2], groups[3]
        param_values_list = (
            [value.strip() for value in param_values.split(",")] if param_values is not None else []
        )
        expanded_gate_body = gate_body
        qubits_usage = [qubit.strip() for qubit in re.findall(r"q\[\d+\]", qubits_usage)]

        for param, value in zip(params_list, param_values_list):
            expanded_gate_body = expanded_gate_body.replace(param, value)

        for qubit, qubit_usage in zip(qubits, qubits_usage):
            expanded_gate_body = expanded_gate_body.replace(qubit, qubit_usage)

        # Replace gate usage with the expanded gate body in the input string
        qasm_string = qasm_string.replace(gate_usage_match.group(0), expanded_gate_body + ";")

        # Search for the next gate usage
        gate_usage_match = gate_usage_pattern.search(qasm_string)

    # Remove double semicolons
    qasm_string = _format_qasm_string(qasm_string, gate_definition_pattern)

    return qasm_string


def _find_gate_line(lines):
    for i, line in enumerate(lines):
        if line.strip().startswith("gate"):
            return i
    return None


def _convert_to_supported_qasm(qasm_str):
    """Dev version of convert_to_supported_qasm function, compatible
    with qiskit>=0.43.0. Returns a copy of the input QASM compatible with
    the :class:`~qbraid.transpiler.cirq_qasm.qasm_parser.QasmParser`.
    Conversion includes deconstruction of custom defined gates, and
    decomposition of unsupported gates/operations.

    """
    # temp hack to fix 'r' replacing last char of 'ecr'
    qasm_str = qasm_str.replace("ecr", "ecr_")

    input_str = _remove_barriers(qasm_str)

    lines = input_str.strip("\n").split("\n")
    gate_lines = [(i, line) for i, line in enumerate(lines) if line.strip().startswith("gate")]
    gate_lines.reverse()  # Reverse to start removing from the last
    gate_line_idx = _find_gate_line(lines)

    # Remove all 'gate' lines
    for idx, _ in gate_lines:
        lines.pop(idx)

    for _, gate_line in gate_lines:
        # Insert the current 'gate' line for this iteration
        lines.insert(gate_line_idx, gate_line)

        new_input = "\n".join(lines)
        new_input = _convert_gate_defs(new_input)  # call the conversion function
        lines = new_input.split("\n")  # update lines after conversion

        # Remove the current 'gate' line for the next iteration
        lines.pop(gate_line_idx)

    return "\n".join(lines)


def convert_to_supported_qasm(qasm_str: str) -> str:
    qasm_lst_out = []
    qasm = _convert_to_supported_qasm(qasm_str)
    qasm_lst = qasm.split("\n")

    for _, qasm_line in enumerate(qasm_lst):
        line_str = qasm_line
        len_line = len(line_str)
        # decompose cu gate into supported gates
        if len_line > 3 and line_str[0:3] == "cu(":
            line_str_out = _decompose_cu_instr(line_str)
        # decompose rxx gate into supported gates
        elif len_line > 4 and line_str[0:4] == "rxx(":
            line_str_out = _decompose_rxx_instr(line_str)
        elif len_line > 4 and line_str[0:4] == "rccx":
            line_str_out = _decompose_rccx_instr(line_str)
        elif len_line > 7 and line_str[0:7] == "c3sqrtx":
            line_str_out = _decompose_c3sqrtx_instr(line_str)
        else:
            line_str_out = line_str

        qasm_lst_out.append(line_str_out)

    qasm_str_def = "\n".join(qasm_lst_out)
    return qasm_str_def


def test_circuit_equality():
    count = 0
    errors = []
    non_equal_circuits = []

    total = 50
    for _ in range(total):
        try:
            qiskit_circuit = random_circuit(num_qubits=4, depth=1)
            qasm = qiskit_circuit.qasm()
            qasm_out = convert_to_supported_qasm(qasm)
            cirq_circuit = _convert_to_line_qubits(
                QasmParser().parse(qasm_out).circuit, rev_qubits=True
            )
            equal = circuits_allclose(qiskit_circuit, cirq_circuit)
            if not equal:
                print(qiskit_circuit)
                print(cirq_circuit)

            if not equal:
                non_equal_circuits.append((qasm, qasm_out))
            else:
                count += 1

        except Exception as err:
            errors.append((qasm, qasm_out, err))

    print(f"Passed {count}/{total} tests")

    if non_equal_circuits:
        print(f"\n{len(non_equal_circuits)} non-equal circuits found:")
        for qasm, qasm_out in non_equal_circuits:
            print(f"\nQASM:\n{qasm}\n\nQASM_OUT:\n{qasm_out}\n\nNot Equal")

    if errors:
        print(f"\n{len(errors)} errors occurred:")
        for qasm, qasm_out, err in errors:
            print(f"\nQASM:\n{qasm}\n\nQASM_OUT:\n{qasm_out}\n\nError: {err}")


qasm_0 = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
cu(5.64196838664496,3.6007731777948906,3.730884212463305, 5.683833391913177) q[1],q[0];
"""

qasm_1 = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
rccx q[1],q[2],q[0];
"""

qasm_2 = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
c3sqrtx q[3],q[1],q[2],q[0];
"""

qasm = qasm_2
qasm_out = convert_to_supported_qasm(qasm)
print(qasm)
print()
print(qasm_out)
qiskit_circuit = QuantumCircuit.from_qasm_str(qasm_out)
print(qiskit_circuit)
print()
cirq_circuit = _convert_to_line_qubits(QasmParser().parse(qasm_out).circuit, rev_qubits=True)
print(cirq_circuit)
print()
equal = circuits_allclose(qiskit_circuit, cirq_circuit)
print(f"equal: {equal}")

# test_circuit_equality()

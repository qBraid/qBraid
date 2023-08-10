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

from qbraid.interface.qbraid_qasm.qelib1_defs import replace_qelib1_defs


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


def convert_to_supported_qasm(qasm_str):
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

    qasm = "\n".join(lines)
    qasm_out = replace_qelib1_defs(qasm)

    return qasm_out

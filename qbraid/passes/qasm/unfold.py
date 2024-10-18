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
Module for preprocessing qasm string to before it is passed to parser.

"""
import re

from .compat import remove_qasm_barriers
from .decompose import decompose_qasm2
from .format import format_qasm


def _unfold_gate_defs(qasm: str) -> str:
    """Recursively expands gate definitions in the input OpenQASM string."""
    # Define regular expression patterns
    gate_definition_pattern = re.compile(
        r"gate ([a-zA-Z0-9_]+)(\((.*?)\))? ((q[0-9]+,)*q[0-9]+) {(.*?)}"
    )

    gate_body = ""
    params_list = []
    gate_usage_match = None

    # Find gate definition and extract its components
    gate_definition_match = gate_definition_pattern.search(qasm)
    if gate_definition_match:
        gate_name, _, params, qubits, _, gate_body = gate_definition_match.groups()
        params_list = [param.strip() for param in params.split(",")] if params is not None else []

        qubits = [qubit.strip() for qubit in qubits.split(",")]

        # pylint: disable=consider-using-f-string
        gate_usage_pattern = re.compile(
            r"({})(\((.*?)\))? ((q\[([0-9]+)\],)*(q\[([0-9]+)\]));".format(gate_name)
        )

        # Replace parameters with their values in gate body
        gate_usage_match = gate_usage_pattern.search(qasm)

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
        qasm = qasm.replace(gate_usage_match.group(0), expanded_gate_body + ";")

        # Search for the next gate usage
        gate_usage_match = gate_usage_pattern.search(qasm)

    # Remove double semicolons
    qasm = format_qasm(qasm, gate_definition_pattern)

    return qasm


def _find_gate_line(lines):
    for i, line in enumerate(lines):
        if line.strip().startswith("gate"):
            return i
    return None


def unfold_qasm2(qasm: str) -> str:
    """Returns a QASM copy with custom gates deconstructed and unsupported operations decomposed."""
    # temp hack to fix 'r' replacing last char of 'ecr'
    qasm = qasm.replace("ecr", "ecr_")

    input_str = remove_qasm_barriers(qasm)

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
        new_input = _unfold_gate_defs(new_input)  # call the conversion function
        lines = new_input.split("\n")  # update lines after conversion

        # Remove the current 'gate' line for the next iteration
        lines.pop(gate_line_idx)

    qasm = "\n".join(lines)
    qasm_out = decompose_qasm2(qasm)

    return qasm_out

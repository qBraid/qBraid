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
Module for providing transforamtions to ensure consistency
in the way OpenQASM 3 strings are formatted.

"""

import re


def _remove_empty_lines(input_string: str) -> str:
    """Removes all empty lines from the provided string."""
    return "\n".join(line for line in input_string.split("\n") if line.strip())


def _remove_double_empty_lines(qasm: str) -> str:
    """Replace double empty lines with single lines from a QASM string."""
    return re.sub(r"\n\n\n", "\n\n", qasm)


def _remove_gate_definition(qasm: str, gate_name: str) -> str:
    """Remove a gate definition from a QASM string."""
    lines = iter(qasm.split("\n"))
    new_qasm = ""

    for line in lines:
        if re.search(r"gate\s+(\w+)", line) is not None:
            # extract the gate name
            current_gate_name = re.search(r"gate\s+(\w+)", line).group(1)
            # remove lines from start curly brace to end curly brace
            if current_gate_name == gate_name:
                while "}" not in line:
                    line = next(lines)
            else:
                new_qasm += line + "\n"
        else:
            new_qasm += line + "\n"

    new_qasm = _remove_double_empty_lines(new_qasm)

    return new_qasm.strip()


def remove_unused_gates(qasm: str) -> str:
    """Remove unused gate definitions from a QASM string."""
    lines = iter(qasm.split("\n"))
    all_gates = {}

    for line in lines:
        if re.search(r"^\s*gate\s+(\w+)", line) is not None:
            gate_name = re.search(r"^\s*gate\s+(\w+)", line).group(1)
            all_gates[gate_name] = -1
        for gate in all_gates:
            if re.search(r"\b" + re.escape(gate) + r"\b", line):
                all_gates[gate] += 1

    new_qasm = qasm
    unused_gates = [gate for gate, count in all_gates.items() if count == 0]
    for gate in unused_gates:
        new_qasm = _remove_gate_definition(new_qasm, gate)

    if len(unused_gates) > 0:
        return remove_unused_gates(new_qasm)

    return new_qasm.strip()

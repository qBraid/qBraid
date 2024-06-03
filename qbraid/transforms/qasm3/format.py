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
                while "{" not in line:
                    line = next(lines)
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
        if any(gate in line for gate in all_gates):
            for gate in all_gates:
                if gate in line:
                    all_gates[gate] += 1

    unused_gates = [
        gate for gate in all_gates if all_gates[gate] == 0
    ]  # pylint: disable=consider-using-dict-items
    new_qasm = qasm
    for gate in unused_gates:
        new_qasm = _remove_gate_definition(new_qasm, gate)
    return remove_unused_gates(new_qasm) if len(unused_gates) > 0 else new_qasm.strip()
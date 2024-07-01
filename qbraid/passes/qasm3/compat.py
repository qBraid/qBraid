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
Module for providing transforamtions to ensure OpenQASM 3 compatibility
across various other quantum software frameworks.

"""
import math
import re
from functools import reduce

GATE_DEFINITIONS = {
    "iswap": """
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
}""",
    "sxdg": """
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}""",
}


def insert_gate_def(qasm3_str: str, gate_name: str, force_insert: bool = False) -> str:
    """Add gate definitions to an Open0QASM 3 string.

    Args:
        qasm3_str (str): QASM 3.0 string.
        gate_name (str): Name of the gate to insert.
        force_insert (bool): If True, the gate definition will be added
            even if the gate is never referenced. Defaults to False.

    Returns:
        str: QASM 3.0 string with gate definition.

    Raises:
        ValueError: If the gate definition is not found.
    """
    defn = GATE_DEFINITIONS.get(gate_name)

    if defn is None:
        raise ValueError(
            f"Gate {gate_name} definition not found. "
            f"Available gate definitions include: {set(GATE_DEFINITIONS.keys())}"
        )

    if not force_insert and gate_name not in qasm3_str:
        return qasm3_str

    lines = qasm3_str.splitlines()

    insert_index = 0
    for i, line in enumerate(lines):
        if "include" in line or "OPENQASM" in line:
            insert_index = i + 1
            break

    lines.insert(insert_index, defn.strip())

    return "\n".join(lines)


def replace_gate_name(
    qasm: str, old_gate_name: str, new_gate_name: str, force_replace: bool = False
) -> str:
    """
    Replace occurrences of a specified gate name in a QASM program string with
    a new gate name, while optionally enforcing the replacement even if the new
    gate name isn't in the predefined gate map.

    Args:
        qasm (str): The QASM program as a string.
        old_gate_name (str): The original gate name to replace.
        new_gate_name (str): The new gate name to use in replacement.
        force_replace (bool): If True, force the replacement even if the
            new gate name isn't in the gate map.

    Returns:
        str: The modified QASM program with the gate names replaced.
    """
    # Define pairs of interchangeable gates
    gate_pairs = [
        ("cnot", "cx"),
        ("si", "sdg"),
        ("ti", "tdg"),
        ("v", "sx"),
        ("vi", "sxdg"),
        ("p", "phaseshift"),
        ("cp", "cphaseshift"),
    ]

    # Create a mapping from each gate to its alternate form
    gate_map = {old: new for pair in gate_pairs for old, new in (pair, pair[::-1])}

    parameterized_gates = {"p", "cp", "phaseshift", "cphaseshift"}

    suffix = "(" if old_gate_name in parameterized_gates else " "

    # Replace based on gate map and force_replace flag
    if old_gate_name in gate_map and (gate_map[old_gate_name] == new_gate_name or force_replace):
        new_gate_name_with_suffix = new_gate_name + suffix
        old_gate_name_with_suffix = old_gate_name + suffix
        return qasm.replace(old_gate_name_with_suffix, new_gate_name_with_suffix)

    if force_replace:
        return qasm.replace(old_gate_name, new_gate_name)

    return qasm


def add_stdgates_include(qasm_str: str) -> str:
    """Add 'include "stdgates.inc";' to the QASM string if it is missing."""
    if 'include "stdgates.inc";' in qasm_str:
        return qasm_str

    lines = qasm_str.splitlines()

    for i, line in enumerate(lines):
        if "OPENQASM" in line:
            lines.insert(i + 1, 'include "stdgates.inc";')
            break

    return "\n".join(lines)


def remove_stdgates_include(qasm: str) -> str:
    """Remove 'include "stdgates.inc";' from the QASM string."""
    return qasm.replace('include "stdgates.inc";', "")


def _evaluate_expression(match):
    """Helper function for simplifying arithmetic expressions within parentheses."""
    expr = match.group(1)
    try:
        simplified_value = eval(expr)  # pylint: disable=eval-used
        return f"({simplified_value})"
    except SyntaxError:
        return match.group(0)


def simplify_arithmetic_expressions(qasm_str: str) -> str:
    """Simplifies arithmetic expressions within parentheses in a QASM string."""

    pattern = r"\(([0-9+\-*/. ]+)\)"

    return re.sub(pattern, _evaluate_expression, qasm_str)


def convert_qasm_pi_to_decimal(qasm_str: str) -> str:
    """Convert all instances of 'pi' in the QASM string to their decimal value."""

    pattern = r"(\d*\.?\d*\s*[*/+-]\s*)?pi(\s*[*/+-]\s*\d*\.?\d*)?"
    # pattern = r"(\d*\.?\d*\s*[*/+-]\s*)*pi(\s*[*/+-]\s*\d*\.?\d*)*"
    # pattern = r"([+-]?(\d+(\.\d*)?)?\s*[*/]\s*)*pi(\s*[*/+-]\s*[+-]?(\d+(\.\d*)?)?)*"

    def replace_with_decimal(match):
        expr = match.group()
        expr_with_pi_as_decimal = expr.replace("pi", str(math.pi))
        try:
            value = eval(expr_with_pi_as_decimal)  # pylint: disable=eval-used
        except SyntaxError:
            return expr
        return str(value)

    return re.sub(pattern, replace_with_decimal, qasm_str)


def has_redundant_parentheses(qasm_str: str) -> bool:
    """Checks if a QASM string contains gate parameters with redundant parentheses."""

    pattern = r"\w+\(\(\s*[-+]?\d+(\.\d*)?\s*\)\)"
    if re.search(pattern, qasm_str):
        return True

    pattern_neg = r"\w+\(-\(\d*\.?\d+\)\)"
    if re.search(pattern_neg, qasm_str):
        return True

    return False


def simplify_parentheses_in_qasm(qasm_str: str) -> str:
    """Simplifies unnecessary parentheses around numbers in QASM strings."""

    lines = qasm_str.splitlines()
    simplified_lines = []

    pattern = r"\(\s*([-+]?\s*\d+(\.\d*)?)\s*\)"

    def simplify(match):
        return match.group(1).replace(" ", "")

    for line in lines:
        if has_redundant_parentheses(line):
            line = re.sub(pattern, simplify, line)
        simplified_lines.append(line)

    return "\n".join(simplified_lines)


def compose(*functions):
    """Compose multiple functions left to right."""

    def compose_two(f, g):
        return lambda x: g(f(x))

    return reduce(compose_two, functions, lambda x: x)


def normalize_qasm_gate_params(qasm: str) -> str:
    """Normalize the parameters of the gates in the QASM string using function composition."""
    transform_qasm = compose(
        convert_qasm_pi_to_decimal, simplify_arithmetic_expressions, simplify_parentheses_in_qasm
    )
    return transform_qasm(qasm)

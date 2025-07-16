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

from openqasm3 import dumps, parse
from openqasm3.ast import Program, QuantumGate, Statement
from openqasm3.parser import QASM3ParsingError

from qbraid._logging import logger

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
    "cv": """
gate cv _gate_q_0, _gate_q_1 {
  ctrl @ sx _gate_q_0, _gate_q_1;
}""",
}


def _insert_gate_def(qasm3_str: str, defn: str) -> str:
    """Add single gate definition to an OpenQASM3 string."""

    lines = qasm3_str.splitlines()

    # Note: In future move gate definition after include statement.
    insert_index = 0
    for i, line in enumerate(lines):
        if "include" in line or "OPENQASM" in line:
            insert_index = i + 1
            break

    lines.insert(insert_index, defn.strip())

    return "\n".join(lines)


def insert_gate_def(qasm3_str: str, gate_name: str | list[str], force_insert: bool = False) -> str:
    """Add gate definitions to an OpenQASM3 string.

    Args:
        qasm3_str (str): QASM 3.0 string.
        gate_name (str | list[str]): Name(s) of the gate(s) to insert.
        force_insert (bool): If True, the gate definition will be added
            even if the gate is never referenced. Defaults to False.

    Returns:
        str: QASM 3.0 string with gate definition.

    Raises:
        ValueError: If the gate definition is not found.
    """
    # Normalize gate_name to a list
    gate_names = [gate_name] if isinstance(gate_name, str) else gate_name

    # Check for missing definitions
    missing = [name for name in gate_names if name not in GATE_DEFINITIONS]
    if missing:
        raise ValueError(
            f"Gate definitions not found for: {missing}. "
            f"Available gate definitions include: {set(GATE_DEFINITIONS.keys())}"
        )

    # Determine which gates to actually add
    gates_to_add = []
    if force_insert:
        gates_to_add = gate_names
    else:
        # Only add if gate name appears in QASM string
        for name in gate_names:
            if name in qasm3_str:
                gates_to_add.append(name)

        # If no gates referenced and force_insert is False, return original
        if not gates_to_add:
            return qasm3_str

    # Insert definitions
    for name in gates_to_add:
        defn = GATE_DEFINITIONS[name]
        qasm3_str = _insert_gate_def(qasm3_str, defn)

    return qasm3_str


def _normalize_case_insensitive_map(gate_mappings: dict[str, str]) -> dict[str, str]:
    """Normalize gate_mappings keys to lowercase and check for duplicates."""
    lowercased_map = {}
    for key, value in gate_mappings.items():
        lower_key = key.lower()
        if lower_key in lowercased_map:
            raise ValueError(
                f"Duplicate key detected after lowercasing: '{lower_key}'. Use case_sensitive=True."
            )
        lowercased_map[lower_key] = value
    return lowercased_map


def _replace_gate_in_statement(
    statement: Statement, gate_mappings: dict[str, str], case_sensitive: bool
) -> QuantumGate:
    """Replace gate names in a single statement if applicable."""
    if isinstance(statement, QuantumGate):
        gate_name = statement.name.name
        lookup_name = gate_name if case_sensitive else gate_name.lower()
        if lookup_name in gate_mappings:
            statement.name.name = gate_mappings[lookup_name]
    return statement


def _replace_gate_names(
    program: Program, gate_mappings: dict[str, str], case_sensitive: bool
) -> Program:
    """Replace occurrences of specified gate names in a openqasm3.ast.Program."""
    if not case_sensitive:
        gate_mappings = _normalize_case_insensitive_map(gate_mappings)

    statements = [
        _replace_gate_in_statement(stmnt, gate_mappings, case_sensitive)
        for stmnt in program.statements
    ]

    return Program(statements=statements, version=program.version)


def replace_gate_names(
    qasm: str, gate_mappings: dict[str, str], case_sensitive: bool = False
) -> str:
    """Replace occurrences of specified gate names in a QASM program string.

    Args:
        qasm (str): The QASM program as a string.
        gate_mappings (dict[str, str]): A dictionary mapping old gate names (keys)
            to new gate names (values).
        case_sensitive (bool): Whether the gate name replacement should be case-sensitive.
            Defaults to False.

    Returns:
        str: The modified QASM program with the gate names replaced.

    Raises:
        ValueError: If duplicate keys are found in the gate_mappings after lowercasing.
    """
    program = parse(qasm)

    program_out = _replace_gate_names(program, gate_mappings, case_sensitive)
    version_major = program_out.version.split(".")[0]
    qasm_out = dumps(program_out)

    if int(version_major) == 2:
        qasm_out = declarations_to_qasm2(qasm_out)

    return qasm_out


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


def convert_qasm_pi_to_decimal(qasm: str) -> str:
    """Convert all instances of 'pi' in the QASM string to their decimal value."""

    pattern = r"(?<![a-zA-Z])(\d*\.?\d*\s*[*/+-]\s*)?pi(\s*[*/+-]\s*\d*\.?\d*)?(?![a-zA-Z])"

    gate_defs = set()

    try:
        program = parse(qasm)

        for statement in program.statements:
            if isinstance(statement, QuantumGate):
                name = statement.name.name
                if "pi" in name:
                    gate_defs.add(name)
    except QASM3ParsingError as err:
        logger.debug("Failed to parse QASM program for pi conversion: %s", err)

    def replace_with_decimal(match: re.Match) -> str:
        expr: str = match.group()
        start = match.start()
        end = match.end()

        for gate_def in gate_defs:
            if gate_def in qasm[max(0, start - len(gate_def)) : end]:
                return expr  # pragma: no cover

        expr_with_pi_as_decimal = expr.replace("pi", str(math.pi))
        value = eval(expr_with_pi_as_decimal)  # pylint: disable=eval-used
        return str(value)

    return re.sub(pattern, replace_with_decimal, qasm)


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


def declarations_to_qasm2(qasm: str) -> str:
    """Converts QASM 3.0 qubit and bit declarations to QASM 2.0 qreg and creg declarations."""
    for declaration_type, replacement_type in [("qubit", "qreg"), ("bit", "creg")]:
        pattern = rf"{declaration_type}\[(\d+)\]\s+(\w+);"
        replacement = rf"{replacement_type} \2[\1];"
        qasm = re.sub(pattern, replacement, qasm)

    return qasm

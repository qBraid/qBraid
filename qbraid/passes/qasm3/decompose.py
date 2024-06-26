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
Module for providing transforamtions with basis gates.
across various other quantum software frameworks.

"""
from typing import Optional, Union

from openqasm3 import ast, dumps
from openqasm3.parser import QASM3ParsingError, parse

from qbraid.passes.exceptions import CompilationError, QasmDecompositionError


def _decompose_crx(gate: ast.QuantumGate) -> list[ast.Statement]:
    """Decompose a crx gate into its basic gate equivalents."""
    theta = gate.arguments[0]
    control = gate.qubits[0]
    target = gate.qubits[1]

    rz_pos_pi_half = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="rz"),
        arguments=[
            ast.BinaryExpression(
                op=ast.BinaryOperator(17),
                lhs=ast.Identifier(name="pi"),
                rhs=ast.FloatLiteral(value=2),
            )
        ],
        qubits=[target],
    )
    ry_pos_theta_half = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="ry"),
        arguments=[
            ast.BinaryExpression(
                op=ast.BinaryOperator(17), lhs=theta, rhs=ast.FloatLiteral(value=2)
            )
        ],
        qubits=[target],
    )
    cx = ast.QuantumGate(
        modifiers=[], name=ast.Identifier(name="cx"), arguments=[], qubits=[control, target]
    )
    ry_neg_theta_half = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="ry"),
        arguments=[
            ast.BinaryExpression(
                op=ast.BinaryOperator(17),
                lhs=ast.UnaryExpression(ast.UnaryOperator(3), theta),
                rhs=ast.FloatLiteral(value=2),
            )
        ],
        qubits=[target],
    )
    rz_neg_pi_half = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="rz"),
        arguments=[
            ast.BinaryExpression(
                op=ast.BinaryOperator(17),
                lhs=ast.UnaryExpression(ast.UnaryOperator(3), ast.Identifier(name="pi")),
                rhs=ast.FloatLiteral(value=2),
            )
        ],
        qubits=[target],
    )
    return [rz_pos_pi_half, ry_pos_theta_half, cx, ry_neg_theta_half, cx, rz_neg_pi_half]


def _decompose_cry(gate: ast.QuantumGate) -> list[ast.Statement]:
    """Decompose a cry gate into its basic gate equivalents."""
    theta = gate.arguments[0]
    control = gate.qubits[0]
    target = gate.qubits[1]

    ry_pos_theta_half = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="ry"),
        arguments=[
            ast.BinaryExpression(
                op=ast.BinaryOperator(17), lhs=theta, rhs=ast.FloatLiteral(value=2)
            )
        ],
        qubits=[target],
    )
    cx = ast.QuantumGate(
        modifiers=[], name=ast.Identifier(name="cx"), arguments=[], qubits=[control, target]
    )
    ry_neg_theta_half = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="ry"),
        arguments=[
            ast.UnaryExpression(
                ast.UnaryOperator(3),
                ast.BinaryExpression(
                    op=ast.BinaryOperator(17), lhs=theta, rhs=ast.FloatLiteral(value=2)
                ),
            )
        ],
        qubits=[target],
    )
    return [ry_pos_theta_half, cx, ry_neg_theta_half, cx]


def _decompose_crz(gate: ast.QuantumGate) -> list[ast.Statement]:
    """Decompose a cry gate into its basic gate equivalents."""
    theta = gate.arguments[0]
    control = gate.qubits[0]
    target = gate.qubits[1]

    rz_pos_theta_half = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="rz"),
        arguments=[
            ast.BinaryExpression(
                op=ast.BinaryOperator(17), lhs=theta, rhs=ast.FloatLiteral(value=2)
            )
        ],
        qubits=[target],
    )
    cx = ast.QuantumGate(
        modifiers=[], name=ast.Identifier(name="cx"), arguments=[], qubits=[control, target]
    )
    rz_neg_theta_half = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="rz"),
        arguments=[
            ast.UnaryExpression(
                ast.UnaryOperator(3),
                ast.BinaryExpression(
                    op=ast.BinaryOperator(17), lhs=theta, rhs=ast.FloatLiteral(value=2)
                ),
            )
        ],
        qubits=[target],
    )
    return [rz_pos_theta_half, cx, rz_neg_theta_half, cx]


def _decompose_cy(gate: ast.QuantumGate, *args) -> list[ast.Statement]:
    """Decompose a cy gate into its basic gate equivalents."""
    control = gate.qubits[0]
    target = gate.qubits[1]

    cry_pi = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="cry"),
        arguments=[ast.Identifier(name="pi")],
        qubits=[control, target],
    )
    s = ast.QuantumGate(modifiers=[], name=ast.Identifier(name="s"), arguments=[], qubits=[control])
    return decompose(ast.Program(statements=[cry_pi, s]), *args).statements


def _decompose_cz(gate: ast.QuantumGate) -> list[ast.Statement]:
    """Decompose a cz gate into its basic gate equivalents."""
    control = gate.qubits[0]
    target = gate.qubits[1]

    crz_pi = ast.QuantumGate(
        modifiers=[],
        name=ast.Identifier(name="crz"),
        arguments=[ast.Identifier(name="pi")],
        qubits=[control, target],
    )
    s = ast.QuantumGate(modifiers=[], name=ast.Identifier(name="s"), arguments=[], qubits=[control])
    return decompose(ast.Program(statements=[crz_pi, s])).statements


def decompose(program: ast.Program, basis_gates: Optional[set[str]] = None) -> ast.Program:
    """Decompose a program into its basic gate equivalents."""
    decomposition_map = {
        "crx": _decompose_crx,
        "cry": _decompose_cry,
        "crz": _decompose_crz,
        "cy": _decompose_cy,
        "cz": _decompose_cz,
    }

    transformed_statements = []
    for statement in program.statements:
        if isinstance(statement, ast.QuantumGate):
            gate_name = statement.name.name
            if gate_name in decomposition_map and (
                basis_gates is None or gate_name not in basis_gates
            ):
                transformed_statements.extend(decomposition_map[gate_name](statement))
            else:
                transformed_statements.append(statement)
        else:
            transformed_statements.append(statement)

    return ast.Program(statements=transformed_statements, version=program.version)


def assert_gates_in_basis(program: ast.Program, basis_gates: set[str]) -> None:
    """Verify that the program is represented only by gates in the given basis gate set."""
    for statement in program.statements:
        if isinstance(statement, ast.QuantumGate):
            gate_name = statement.name.name
            if gate_name not in basis_gates:
                raise ValueError(
                    f"OpenQASM program uses gate '{gate_name}' which is not in the basis gate set."
                )


def rebase(qasm: str, basis_gates: Union[set[str], str], require_predicates: bool = True) -> str:
    """
    Rebases an OpenQASM 3 program according to a given basis gate set.

    Args:
        qasm (str): The original OpenQASM 3 program as a string.
        basis_gates (set[str]): The target basis gates to decompose the program to.
        require_predicates (bool): If True, raises an error if the program fails to meet compilation
            predicates. If False, returns the original program on failure. Defaults to True.

    Returns:
        str: The decomposed OpenQASM 3 program.

    Raises:
        ValueError: If no basis gates are provided or if the basis gate set identifier is invalid
        TypeError: If the basis gate set is not a set of strings or a string identifier
        QasmDecompositionError: If an error occurrs during the decomposition process
        CompilationError: If the program cannot be rebased to the provided basis gate set

    """
    # Validate basis gates
    if isinstance(basis_gates, set):
        if len(basis_gates) == 0:
            raise ValueError("Basis gate set cannot be empty.")
    elif isinstance(basis_gates, str):
        if basis_gates.lower() == "any":
            basis_gates = set()
        else:
            raise ValueError("Invalid basis gate set identifier.")
    else:
        raise TypeError("Basis gate set must be a set of strings or a string identifier.")

    # Parse program and apply decomposition(s)
    try:
        program = parse(qasm)
    except QASM3ParsingError as err:
        raise ValueError("Invalid OpenQASM 3 program.") from err

    try:
        converted_program = decompose(program, basis_gates)
    except Exception as err:  # pylint: disable=broad-exception-caught
        raise QasmDecompositionError from err

    # Check if the program meets the compilation predicates
    try:
        if len(basis_gates) > 0:
            assert_gates_in_basis(converted_program, basis_gates)
    except ValueError as err:
        if require_predicates:
            raise CompilationError(
                "Rebasing the specified quantum program to the provided "
                f"basis gate set {basis_gates} is not supported."
            ) from err

        return qasm

    return dumps(converted_program)


def decompose_qasm3(qasm: str) -> str:
    """Decompose an OpenQASM 3 program."""
    return rebase(qasm, basis_gates="any", require_predicates=False)


__all__ = ["decompose", "decompose_qasm3", "rebase", "assert_gates_in_basis"]

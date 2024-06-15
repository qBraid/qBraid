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
from openqasm3 import ast, dumps
from openqasm3.parser import parse

from qbraid.passes.exceptions import QasmDecompositionError


def decompose_crx(gate: ast.QuantumGate) -> list[ast.Statement]:
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


def decompose_cry(gate: ast.QuantumGate) -> list[ast.Statement]:
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


def decompose_crz(gate: ast.QuantumGate) -> list[ast.Statement]:
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


def decompose_cy(gate: ast.QuantumGate) -> list[ast.Statement]:
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
    return _decompose(ast.Program(statements=[cry_pi, s])).statements


def decompose_cz(gate: ast.QuantumGate) -> list[ast.Statement]:
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
    return _decompose(ast.Program(statements=[crz_pi, s])).statements


def _decompose(program: ast.Program) -> ast.Program:
    """Decompose a program into its basic gate equivalents."""
    transformed_statements = []
    for statement in program.statements:
        if isinstance(statement, ast.QuantumGate):
            if statement.name.name == "crx":
                transformed_statements.extend(decompose_crx(statement))
            elif statement.name.name == "cry":
                transformed_statements.extend(decompose_cry(statement))
            elif statement.name.name == "crz":
                transformed_statements.extend(decompose_crz(statement))
            elif statement.name.name == "cy":
                transformed_statements.extend(decompose_cy(statement))
            elif statement.name.name == "cz":
                transformed_statements.extend(decompose_cz(statement))
            else:
                transformed_statements.append(statement)
        else:
            transformed_statements.append(statement)

    return ast.Program(statements=transformed_statements, version=program.version)


def decompose(qasm: str) -> str:
    """
    Decompose an OpenQASM 3 program to an equivalent program
    using basis gates from the following set:

    ["x","y","z","rx","ry","rz","h","cx","s","sdg","t","tdg","sx","sxdg","swap"]

    Args:
        qasm (str): The original OpenQASM 3 program as a string.

    Returns:
        str: The decomposed OpenQASM 3 program.

    Raises:
        ValueError: if the decomposition is not possible
    """
    program = parse(qasm)

    try:
        converted_program = _decompose(program)
    except Exception as err:  # pylint: disable=broad-exception-caught
        raise QasmDecompositionError from err

    return dumps(converted_program)

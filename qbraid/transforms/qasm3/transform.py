"""Transform Program to program with basis gates."""

import numpy as np
from openqasm3.ast import (
    Program,
    QuantumGate,
    QuantumStatement,
    Identifier,
    FloatLiteral,
    BinaryExpression,
    BinaryOperator,
    UnaryExpression,
    UnaryOperator,
)
from typing import List
from qbraid.transpiler.conversions.openqasm3 import openqasm3_to_qasm3
from openqasm3.parser import parse


def decompose_crx(gate: QuantumGate) -> List[QuantumStatement]:
    """Decompose a crx gate into its basic gate equivalents."""
    theta = gate.arguments[0]
    control = gate.qubits[0]
    target = gate.qubits[1]

    rz_pos_pi_half = QuantumGate(
        modifiers=[],
        name=Identifier(name="rz"),
        arguments=[
            BinaryExpression(op=BinaryOperator(
                17), lhs=Identifier(name="pi"), rhs=FloatLiteral(value=2))
        ],
        qubits=[target],
    )
    ry_pos_theta_half = QuantumGate(
        modifiers=[],
        name=Identifier(name="ry"),
        arguments=[
            BinaryExpression(op=BinaryOperator(
                17), lhs=theta, rhs=FloatLiteral(value=2))
        ],
        qubits=[target],
    )
    cx = QuantumGate(
        modifiers=[], name=Identifier(name="cx"),
        arguments=[],
        qubits=[control, target]
    )
    ry_neg_theta_half = QuantumGate(
        modifiers=[],
        name=Identifier(name="ry"),
        arguments=[
            BinaryExpression(op=BinaryOperator(
                17), lhs=UnaryExpression(UnaryOperator(3), theta), rhs=FloatLiteral(value=2))
        ],
        qubits=[target],
    )
    rz_neg_pi_half = QuantumGate(
        modifiers=[],
        name=Identifier(name="rz"),
        arguments=[
            BinaryExpression(op=BinaryOperator(
                17), lhs=UnaryExpression(UnaryOperator(3), Identifier(name="pi")), rhs=FloatLiteral(value=2))
        ],
        qubits=[target],
    )
    return [rz_pos_pi_half, ry_pos_theta_half, cx, ry_neg_theta_half, cx, rz_neg_pi_half]


def decompose_cry(gate: QuantumGate) -> List[QuantumStatement]:
    """Decompose a cry gate into its basic gate equivalents."""
    theta = gate.arguments[0]
    control = gate.qubits[0]
    target = gate.qubits[1]

    ry_pos_theta_half = QuantumGate(
        modifiers=[],
        name=Identifier(name="ry"),
        arguments=[
            BinaryExpression(op=BinaryOperator(
                17), lhs=theta, rhs=FloatLiteral(value=2))
        ],
        qubits=[target],
    )
    cx = QuantumGate(
        modifiers=[], name=Identifier(name="cx"),
        arguments=[],
        qubits=[control, target]
    )
    ry_neg_theta_half = QuantumGate(
        modifiers=[],
        name=Identifier(name="ry"),
        arguments=[
            UnaryExpression(
                UnaryOperator(3),
                BinaryExpression(
                    op=BinaryOperator(17),
                    lhs=theta,
                    rhs=FloatLiteral(value=2)
                )
            )
        ],
        qubits=[target],
    )
    return [ry_pos_theta_half, cx, ry_neg_theta_half, cx]


def decompose_crz(gate: QuantumGate) -> List[QuantumStatement]:
    """Decompose a cry gate into its basic gate equivalents."""
    theta = gate.arguments[0]
    control = gate.qubits[0]
    target = gate.qubits[1]

    rz_pos_theta_half = QuantumGate(
        modifiers=[],
        name=Identifier(name="rz"),
        arguments=[
            BinaryExpression(op=BinaryOperator(
                17), lhs=theta, rhs=FloatLiteral(value=2))
        ],
        qubits=[target],
    )
    cx = QuantumGate(
        modifiers=[], name=Identifier(name="cx"),
        arguments=[],
        qubits=[control, target]
    )
    rz_neg_theta_half = QuantumGate(
        modifiers=[],
        name=Identifier(name="rz"),
        arguments=[
            UnaryExpression(
                UnaryOperator(3),
                BinaryExpression(
                    op=BinaryOperator(17),
                    lhs=theta,
                    rhs=FloatLiteral(value=2)
                )
            )
        ],
        qubits=[target],
    )
    return [rz_pos_theta_half, cx, rz_neg_theta_half, cx]


def decompose_cy(gate: QuantumGate) -> List[QuantumStatement]:
    """Decompose a cy gate into its basic gate equivalents."""
    control = gate.qubits[0]
    target = gate.qubits[1]

    cry_pi = QuantumGate(
        modifiers=[],
        name=Identifier(name="cry"),
        arguments=[Identifier(name="pi")],
        qubits=[control, target],
    )
    s = QuantumGate(
        modifiers=[], name=Identifier(name="s"),
        arguments=[],
        qubits=[control]
    )
    return transform_program(Program(statements=[cry_pi, s])).statements


def transform_program(program: Program) -> Program:
    """Transform a QASM program, decomposing crx gates."""
    transformed_statements = []
    for statement in program.statements:
        if isinstance(statement, QuantumGate):
            if statement.name.name == "crx":
                transformed_statements.extend(decompose_crx(statement))
            elif statement.name.name == "cry":
                transformed_statements.extend(decompose_cry(statement))
            elif statement.name.name == "crz":
                transformed_statements.extend(decompose_crz(statement))
            elif statement.name.name == "cy":
                transformed_statements.extend(decompose_cy(statement))
            else:
                transformed_statements.append(statement)
        else:
            transformed_statements.append(statement)

    return Program(statements=transformed_statements, version=program.version)


def convert_to_basis_gates(qasm: str, basis_gates: list[str]) -> str:
    """
    Converts an OpenQASM 3 program to an equivalent program that only uses the specified basis gates.

    Args:
        openqasm_program (str): The original OpenQASM 3 program as a string.
        basis_gates (list[str]): A list of gate names allowed in the basis set.

    Returns:
        str: The converted OpenQASM 3 program.

    Raises:
        ValueError: if the decomposition is not possible
    """

    program = parse(qasm)

    converted_program = transform_program(program)

    return openqasm3_to_qasm3(converted_program)

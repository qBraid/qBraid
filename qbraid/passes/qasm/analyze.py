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
Functions for analyzing OpenQASM programs.

"""
from __future__ import annotations

from typing import Optional, Union

from openqasm3.ast import (
    BinaryExpression,
    BitType,
    BranchingStatement,
    ClassicalDeclaration,
    Concatenation,
    Expression,
    Identifier,
    IndexedIdentifier,
    IntegerLiteral,
    Program,
    QuantumBarrier,
    QuantumGate,
    QuantumMeasurementStatement,
    QuantumReset,
    QubitDeclaration,
    RangeDefinition,
    Statement,
)
from openqasm3.parser import parse


def has_measurements(program: Union[Program, str]) -> bool:
    """Check if the program has any measurement operations."""
    program = parse(program) if isinstance(program, str) else program
    for statement in program.statements:
        if isinstance(statement, QuantumMeasurementStatement):
            return True
    return False


def expression_value(expression: Optional[Union[Expression, RangeDefinition]]) -> int:
    """Return the size of an expression."""
    if isinstance(expression, IntegerLiteral):
        return expression.value

    raise ValueError(f"Invalid expression type: {type(expression)}. Expected IntegerLiteral.")


def expression_value_option(expression: Optional[Expression]) -> Optional[int]:
    """Return the size of an expression."""
    if expression is None:
        return None

    return expression_value(expression)


# pylint: disable-next=too-many-statements
def depth(
    qasm_statements: list[Statement], counts: dict[tuple[str, int], int]
) -> dict[tuple[str, int], int]:
    """Return the depth of a list of given qasm statements."""
    qreg_sizes = {}
    creg_sizes = {}
    track_measured = {}
    max_depth = 0
    # pylint: disable-next=too-many-nested-blocks
    for statement in qasm_statements:
        if isinstance(statement, QubitDeclaration):
            qreg_name = statement.qubit.name
            qreg_size = expression_value(statement.size)
            qreg_sizes[qreg_name] = qreg_size
            continue
        if isinstance(statement, ClassicalDeclaration) and isinstance(statement.type, BitType):
            creg_name = statement.identifier.name
            creg_size: int = expression_value(statement.type.size)
            creg_sizes[creg_name] = creg_size
            for i in range(creg_size):
                track_measured[f"{creg_name}[{i}]"] = 0
            continue
        if isinstance(statement, QuantumGate):
            qubits_involved = set()
            if all(isinstance(qubit, IndexedIdentifier) for qubit in statement.qubits):
                for qubit in statement.qubits:
                    if isinstance(qubit.name, Identifier):
                        qreg_name = qubit.name.name
                        if isinstance(qubit.indices[0], list):
                            expression = qubit.indices[0][0]
                        qubit_index = expression_value(expression)
                        counts[(qreg_name, qubit_index)] += 1
                        qubits_involved.add((qreg_name, qubit_index))
                max_involved_depth = max(counts[qubit] for qubit in qubits_involved)
                for qubit in qubits_involved:
                    counts[qubit] = max_involved_depth
            else:
                for qubit in statement.qubits:
                    qreg_name = str(qubit.name)
                    for i in range(qreg_sizes[qreg_name]):
                        counts[(qreg_name, i)] += 1
            max_depth = max(counts.values())
        elif isinstance(statement, QuantumReset):
            if isinstance(statement.qubits, IndexedIdentifier):
                qreg_name = statement.qubits.name.name
                if isinstance(statement.qubits.indices[0], list):
                    expression = statement.qubits.indices[0][0]
                qubit_index = expression_value(expression)
                counts[(qreg_name, qubit_index)] += 1
            else:
                qreg_name = statement.qubits.name
                for i in range(qreg_sizes[qreg_name]):
                    counts[(qreg_name, i)] += 1
        elif isinstance(statement, QuantumBarrier):
            for qubit_identifier in statement.qubits:
                if isinstance(qubit_identifier, (IndexedIdentifier, Identifier)):
                    qreg_name = str(qubit_identifier.name)
                    for i in range(qreg_sizes[qreg_name]):
                        counts[(qreg_name, i)] = max_depth
        elif isinstance(statement, QuantumMeasurementStatement):
            qubit = statement.measure.qubit
            if isinstance(qubit, IndexedIdentifier):
                qreg_name = qubit.name.name
                if isinstance(qubit.indices[0], list):
                    qubit_expr = qubit.indices[0][0]
                qubit_index = expression_value(qubit_expr)
                counts[(qreg_name, qubit_index)] += 1
                max_depth = max(counts.values())
                if isinstance(statement.target, IndexedIdentifier):
                    if isinstance(statement.target.indices[0], list):
                        creg_expr = statement.target.indices[0][0]
                        creg_index = expression_value(creg_expr)
                        creg_name = statement.target.name.name
                        track_measured[(creg_name, creg_index)] = max_depth
            else:
                qreg_name = qubit.name
                for i in range(qreg_sizes[qreg_name]):
                    counts[(qreg_name, i)] += 1
                if isinstance(statement.target, Identifier):
                    creg = str(statement.target.name)
                max_depth = max(counts.values())
                for i in range(creg_sizes[creg]):
                    track_measured[(creg, i)] = max_depth
        elif isinstance(statement, BranchingStatement) and isinstance(
            statement.condition, (BinaryExpression, Concatenation)
        ):
            expression = statement.condition.lhs
            if isinstance(expression, (IndexedIdentifier, Identifier)):
                creg_name = expression.name

                for creg_index in range(creg_sizes[creg_name]):
                    if (creg_name, creg_index) not in track_measured:
                        track_measured[(creg_name, creg_index)] = 0

                required_depth = max(
                    track_measured[(creg_name, creg_index)]
                    for creg_index in range(creg_sizes[creg_name])
                )
                required_depth = max(required_depth, max_depth)
                for i in range(creg_sizes[creg_name]):
                    track_measured[(creg_name, i)] = required_depth
                qubits: set[str] = set()
                for sub_statement in statement.if_block + statement.else_block:
                    if isinstance(sub_statement, QuantumGate):
                        for qubit in sub_statement.qubits:
                            if isinstance(qubit.name, Identifier):
                                qreg_name = qubit.name.name
                            if isinstance(qubit, IndexedIdentifier):
                                if isinstance(qubit.indices[0], list):
                                    expression = qubit.indices[0][0]
                            qubit_index = expression_value(expression)
                            qubits.add((qreg_name, qubit_index))
                    elif isinstance(sub_statement, QuantumMeasurementStatement):
                        if isinstance(sub_statement.measure.qubit.name, Identifier):
                            qreg_name = sub_statement.measure.qubit.name.name
                        if isinstance(sub_statement.measure.qubit, IndexedIdentifier):
                            if isinstance(sub_statement.measure.qubit.indices[0], list):
                                expression = sub_statement.measure.qubit.indices[0][0]
                        if isinstance(expression, Expression):
                            qubit_index = expression_value(expression)
                            qubits.add((qreg_name, qubit_index))

                for qubit_id in qubits:
                    counts[qubit_id] = max(required_depth, counts[qubit_id]) + 1

                max_depth = max(counts.values())
    return counts

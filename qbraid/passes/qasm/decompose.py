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

from .compat import declarations_to_qasm2, remove_spaces_in_parentheses


def _get_param(instr: str) -> Optional[str]:
    try:
        return instr[instr.index("(") + 1 : instr.index(")")]
    except ValueError:
        return None


def _decompose_cu_instr(instr: str) -> str:
    """controlled-U gate"""
    try:
        instr = remove_spaces_in_parentheses(instr)
        cu_gate, qs = instr.split(" ")
        a, b = qs.strip(";").split(",")
        params_lst = _get_param(cu_gate).split(",")
        params = [float(x) for x in params_lst]
        theta, phi, lam, gamma = params
    except (AttributeError, ValueError) as err:
        raise QasmDecompositionError from err
    instr_out = "\n// cu gate\n"
    instr_out += f"p({gamma}) {a};\n"
    instr_out += f"p({(lam+phi)/2}) {a};\n"
    instr_out += f"p({(lam-phi)/2}) {b};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out += f"u({-1*theta/2},0,{-1*(phi+lam)/2}) {b};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out += f"u({theta/2},{phi},0) {b};\n\n"
    return instr_out


def _decompose_rxx_instr(instr: str) -> str:
    """two-qubit XX rotation"""
    try:
        instr = instr.replace(", ", ",")
        rxx_gate, qs = instr.split(" ")
        a, b = qs.strip(";").split(",")
        theta = _get_param(rxx_gate)
    except (AttributeError, ValueError) as err:
        raise QasmDecompositionError from err
    instr_out = "\n// rxx gate\n"
    instr_out += f"h {a};\n"
    instr_out += f"h {b};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out += f"rz({theta}) {b};\n"
    instr_out += f"cx {a},{b};\n"
    instr_out += f"h {b};\n"
    instr_out += f"h {a};\n\n"
    return instr_out


def _decompose_rccx_instr(instr: str) -> str:
    """relative-phase CCX"""
    try:
        _, qs = instr.split(" ")
        a, b, c = qs.strip(";").split(",")
    except (AttributeError, ValueError) as err:
        raise QasmDecompositionError from err
    instr_out = "\n// rccx gate\n"
    instr_out += f"u2(0,pi) {c};\n"
    instr_out += f"u1(pi/4) {c};\n"
    instr_out += f"cx {b},{c};\n"
    instr_out += f"u1(-pi/4) {c};\n"
    instr_out += f"cx {a},{c};\n"
    instr_out += f"u1(pi/4) {c};\n"
    instr_out += f"cx {b},{c};\n"
    instr_out += f"u1(-pi/4) {c};\n"
    instr_out += f"u2(0,pi) {c};\n\n"
    return instr_out


def _decompose_rc3x_instr(instr: str) -> str:
    """relative-phase 3-controlled X gate"""
    try:
        _, qs = instr.split(" ")
        a, b, c, d = qs.strip(";").split(",")
    except (AttributeError, ValueError) as err:
        raise QasmDecompositionError from err
    instr_out = "\n// rc3x gate\n"
    instr_out += f"u2(0,pi) {d};\n"
    instr_out += f"u1(pi/4) {d};\n"
    instr_out += f"cx {c},{d};\n"
    instr_out += f"u1(-pi/4) {d};\n"
    instr_out += f"u2(0,pi) {d};\n"
    instr_out += f"cx {a},{d};\n"
    instr_out += f"u1(pi/4) {d};\n"
    instr_out += f"cx {b},{d};\n"
    instr_out += f"u1(-pi/4) {d};\n"
    instr_out += f"cx {a},{d};\n"
    instr_out += f"u1(pi/4) {d};\n"
    instr_out += f"cx {b},{d};\n"
    instr_out += f"u1(-pi/4) {d};\n"
    instr_out += f"u2(0,pi) {d};\n"
    instr_out += f"u1(pi/4) {d};\n"
    instr_out += f"cx {c},{d};\n"
    instr_out += f"u1(-pi/4) {d};\n"
    instr_out += f"u2(0,pi) {d};\n\n"
    return instr_out


def decompose_qasm2(qasm: str) -> str:
    """Replace edge-case qelib1 gates with equivalent decomposition."""
    qasm_lst_out = []
    qasm_lst = qasm.split("\n")

    for _, qasm_line in enumerate(qasm_lst):
        line_str = qasm_line
        len_line = len(line_str)
        if len_line > 3 and line_str[0:3] == "cu(":
            line_str_out = _decompose_cu_instr(line_str)
        elif len_line > 4 and line_str[0:4] == "rxx(":
            line_str_out = _decompose_rxx_instr(line_str)
        elif len_line > 4 and line_str[0:4] == "rccx":
            line_str_out = _decompose_rccx_instr(line_str)
        elif len_line > 4 and line_str[0:4] == "rc3x":
            line_str_out = _decompose_rc3x_instr(line_str)
        else:
            line_str_out = line_str

        qasm_lst_out.append(line_str_out)

    qasm_str_def = "\n".join(qasm_lst_out)
    return qasm_str_def


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
        raise ValueError("Invalid OpenQASM program.") from err

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

    version_major = converted_program.version.split(".")[0]
    qasm = dumps(converted_program)

    if int(version_major) == 2:
        qasm = declarations_to_qasm2(qasm)

    return qasm


def decompose_qasm3(qasm: str) -> str:
    """Decompose an OpenQASM 3 program."""
    return rebase(qasm, basis_gates="any", require_predicates=False)


__all__ = ["decompose", "decompose_qasm2", "decompose_qasm3", "rebase", "assert_gates_in_basis"]

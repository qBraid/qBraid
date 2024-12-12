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
Module containing OpenQASM to CUDA-Q conversion function

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Union

import pyqasm
from openqasm3 import ast, parser, printer
from qbraid_core._import import LazyLoader

from qbraid.passes.qasm import normalize_qasm_gate_params
from qbraid.transpiler.annotations import requires_extras, weight
from qbraid.transpiler.exceptions import ProgramConversionError

cudaq = LazyLoader("cudaq", globals(), "cudaq")

if TYPE_CHECKING:
    from cudaq import PyKernel, QuakeValue


def gate_kernel(name: str, *args) -> PyKernel:
    """Returns CUDA-Q kernel for pure standard gates (no modifiers - ctrl or adj)."""

    if name in ["x", "y", "z", "h", "s", "t", "sdg", "tdg", "i", "id", "iden"]:
        size, argc = 1, 0
    elif name in ["rx", "ry", "rz"]:
        size, argc = 1, 1
    elif name in ["swap"]:
        size, argc = 2, 0
    elif name in ["u3"]:
        size, argc = 3, 3
    else:
        raise ProgramConversionError(f"Unsupported gate: {name}")

    kernel, *qrefs = cudaq.make_kernel(*[cudaq.qubit for _ in range(size)])

    if len(args) != argc:
        raise ProgramConversionError(
            f"Gate {name} requires {argc} args but only {len(args)} were provided: {args}"
        )

    if name in ["i", "id", "iden"]:
        return kernel

    op = getattr(kernel, name)

    if len(args) > 0:
        op(*args, *qrefs)
    else:
        op(*qrefs)

    return kernel


def identifier_lookup(cbit: Union[ast.IndexedIdentifier, ast.Identifier]) -> str:
    """Unpacks the identifier name"""
    if isinstance(cbit, ast.IndexedIdentifier):
        return cbit.name.name

    return cbit.name


@weight(1)
@requires_extras("cudaq")
# pylint: disable-next=too-many-statements
def openqasm3_to_cudaq(program: ast.Program) -> PyKernel:
    """Returns a CUDA-Q kernel representing the input OpenQASM program.

    Args:
        qasm (str or ast.Program): OpenQASM program to convert to CUDA-Q kernel.

    Returns:
        kernel: CUDA-Q kernel equivalent to input OpenQASM string.
    """
    try:
        module = pyqasm.load(program)
        module.validate()
    except Exception as e:
        raise ProgramConversionError("PyQasm program is not well-formed") from e

    module.unroll()
    program = module.unrolled_ast
    program = parser.parse(normalize_qasm_gate_params(printer.dumps(program)))

    kernel: PyKernel = cudaq.make_kernel()
    ctx: Dict[str, Union[QuakeValue | None]] = {}

    def qubit_lookup(qubit: Union[ast.IndexedIdentifier, ast.Identifier]) -> QuakeValue:
        if isinstance(qubit, ast.IndexedIdentifier):
            if len(qubit.indices) > 1:
                raise ProgramConversionError(
                    f"Multi-dimensional array indexing is unsupported: {qubit.indices}"
                )

            inds = qubit.indices[0]
            if isinstance(inds, ast.DiscreteSet):
                inds = inds.values

            if len(inds) > 1:
                raise ProgramConversionError(
                    f"Discrete set or multi-integer indexing is unsupported: {inds}"
                )

            ind = inds[0]
            if not isinstance(ind, ast.IntegerLiteral):
                raise ProgramConversionError(f"Index must be a single integer literal: {ind}")

            q = ctx[qubit.name.name][ind.value]
        else:
            assert isinstance(qubit, ast.Identifier)
            q = ctx[qubit.name][0]
        return q

    # pylint: disable-next=too-many-nested-blocks
    for statement in program.statements:
        if isinstance(statement, ast.Include):
            if statement.filename not in {"stdgates.inc", "qelib1.inc"}:
                raise ProgramConversionError(f"Includes are unsupported: {statement}")
        elif isinstance(statement, ast.QubitDeclaration):
            ctx[statement.qubit.name] = kernel.qalloc(statement.size.value)
        elif isinstance(statement, ast.ClassicalDeclaration):
            if not isinstance(statement.type, ast.ClassicalType):
                raise ProgramConversionError(f"Unsupported statement: {statement}")

            if statement.init_expression and isinstance(
                statement.init_expression, ast.QuantumMeasurement
            ):
                ctx[statement.identifier.name] = kernel.mz(
                    qubit_lookup(statement.init_expression.qubit)
                )
            else:
                ctx[statement.identifier.name] = None
        elif isinstance(statement, ast.QuantumMeasurementStatement):
            val = kernel.mz(qubit_lookup(statement.measure.qubit))
            if statement.target is not None:
                ctx[identifier_lookup(statement.target)] = val
        elif isinstance(statement, ast.QuantumGate):
            name, qubits = statement.name.name, statement.qubits

            args = []
            for arg in statement.arguments:
                if arg.value is None:
                    raise ProgramConversionError(
                        f"Non-literal gate arguments are unsupported. {statement.arguments}"
                    )
                args.append(arg.value)

            qubit_refs = [qubit_lookup(q) for q in qubits]

            if len(statement.modifiers) > 1:
                raise ProgramConversionError(
                    f"Multiple gate modifiers are unsupported: {statement}"
                )
            if len(statement.modifiers) == 1:
                mod = statement.modifiers[0]
                if mod.modifier != ast.GateModifierName.ctrl:
                    raise ProgramConversionError(f"Non-ctrl modifiers are unsupported: {statement}")

                gate = gate_kernel(name, *args)
                kernel.control(gate, qubit_refs[0], *qubit_refs[1:])
            else:
                if (namel := name.lower())[0] == "c" and namel[1:] in [
                    "x",
                    "y",
                    "z",
                    "rx",
                    "ry",
                    "rz",
                ]:
                    # TODO: pyqasm doesn't unroll C{X,Y,Z} -> ctrl @ x. the below also handles this.
                    gate = gate_kernel(namel[1:], *args)
                    kernel.control(gate, qubit_refs[0], *qubit_refs[1:])
                else:
                    gate = gate_kernel(name, *args)
                    kernel.apply_call(gate, *qubit_refs)

        else:
            raise ProgramConversionError(f"Unsupported statement: {statement}")

    return kernel

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
Module defining OpenQASM 3 to CUDA-Q conversion function.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pyqasm
from openqasm3 import ast
from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError

cudaq = LazyLoader("cudaq", globals(), "cudaq")

if TYPE_CHECKING:
    from cudaq import PyKernel, QuakeValue

    from qbraid.programs.typer import QasmStringType


def make_gate_kernel(name: str, targs: tuple[type]) -> PyKernel:
    """Returns CUDA-Q kernel for pure standard gates (no modifiers - ctrl or adj)."""

    if name in [
        "x",
        "y",
        "z",
        "rx",
        "ry",
        "rz",
        "h",
        "s",
        "t",
        "sdg",
        "tdg",
        "u3",
        "i",
        "id",
        "iden",
    ]:
        size = 1
    elif name in ["swap"]:
        size = 2
    else:
        raise ProgramConversionError(f"Unsupported gate: {name}")

    kernel, *qparams = cudaq.make_kernel(*[cudaq.qubit for _ in range(size)], *targs)
    qrefs, qargs = qparams[:size], qparams[size:]

    if name in ["i", "id", "iden"]:
        return kernel

    op = getattr(kernel, name)

    if len(targs) > 0:
        op(*qargs, *qrefs)
    else:
        op(*qrefs)

    return kernel


@weight(0.95)  # pylint: disable-next=too-many-statements
def openqasm3_to_cudaq(program: QasmStringType | ast.Program) -> PyKernel:
    """Returns a CUDA-Q kernel representing the input OpenQASM program.

    Args:
        qasm (str or ast.Program): OpenQASM program to convert to CUDA-Q kernel.

    Returns:
        kernel: CUDA-Q kernel equivalent to input OpenQASM string.
    """
    try:
        module = pyqasm.loads(program)
        module.validate()
    except Exception as e:
        raise ProgramConversionError("QASM program is not well-formed.") from e

    module.unroll()
    program = module.unrolled_ast

    kernel: PyKernel = cudaq.make_kernel()
    ctx: dict[str, Optional[QuakeValue]] = {}
    gate_kernels: dict[str, PyKernel] = {}

    def get_gate(name: str, targs: tuple[type]) -> PyKernel:
        if name in gate_kernels:
            return gate_kernels[name]

        gate_kernels[name] = make_gate_kernel(name, targs)
        return gate_kernels[name]

    def qubit_lookup(qubit: ast.IndexedIdentifier | ast.Identifier) -> QuakeValue:
        assert isinstance(
            qubit, ast.IndexedIdentifier
        ), f"all identifiers should've been indexed: {qubit}"

        assert len(qubit.indices) == 1, f"multi-dim arrays are not supported: {qubit.indices}"

        inds = qubit.indices[0]

        assert len(inds) == 1, f"indices should've been a single integer: {inds}"
        assert isinstance(ind := inds[0], ast.IntegerLiteral)

        q = ctx[qubit.name.name][ind.value]
        return q

    # pylint: disable-next=too-many-nested-blocks
    for statement in program.statements:
        if isinstance(statement, ast.Include):
            if statement.filename not in {"stdgates.inc", "qelib1.inc"}:
                raise ProgramConversionError(f"Custom includes are unsupported: {statement}")
        elif isinstance(statement, ast.QubitDeclaration):
            ctx[statement.qubit.name] = kernel.qalloc(statement.size.value)
        elif isinstance(statement, ast.ClassicalDeclaration):
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
                assert isinstance(
                    statement.target, ast.IndexedIdentifier
                ), f"identifiers should've been unrolled to indexed identifiers: {statement.target}"
                ctx[statement.target.name.name] = val
        elif isinstance(statement, ast.QuantumGate):
            name, qubits = statement.name.name, statement.qubits

            args = []
            for arg in statement.arguments:
                assert arg.value is not None, f"gate arguments should've been literals: {arg}"
                args.append(arg.value)
            targs = [type(a) for a in args]

            qubit_refs = [qubit_lookup(q) for q in qubits]

            # pyqasm unrolls multiple modifiers.
            # ctrl isn't supported so multi-ctrl is not an issue at the moment.
            assert len(statement.modifiers) <= 1

            if len(statement.modifiers) == 1:
                mod = statement.modifiers[0]
                assert (
                    mod.modifier == ast.GateModifierName.ctrl
                ), f"non-ctrl modifiers should've be unrolled: {mod}"

                gate = get_gate(name, targs)
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
                    # pyqasm doesn't unroll C{X,Y,Z} -> ctrl @ x. the below also handles this.
                    gate = get_gate(namel[1:], targs)
                    kernel.control(gate, qubit_refs[0], *qubit_refs[1:], *args)
                else:
                    gate = get_gate(name, targs)
                    kernel.apply_call(gate, *qubit_refs, *args)

        else:
            raise ProgramConversionError(f"Unsupported statement: {statement}")

    return kernel

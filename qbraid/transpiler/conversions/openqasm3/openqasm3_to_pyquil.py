# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module containing OpenQASM 3 AST to pyQuil conversion function.

"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pyqasm
from openqasm3 import ast
from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError

pyquil = LazyLoader("pyquil", globals(), "pyquil")

if TYPE_CHECKING:
    from pyquil import Program

    from qbraid.programs.typer import QasmStringType


def _index_value(identifier: ast.IndexedIdentifier) -> int:
    """Return the single integer index from an unrolled OpenQASM identifier."""
    if not isinstance(identifier, ast.IndexedIdentifier):
        raise ProgramConversionError(f"Expected indexed identifier, got: {identifier}")
    if len(identifier.indices) != 1 or len(identifier.indices[0]) != 1:
        raise ProgramConversionError(f"Unsupported multi-dimensional identifier: {identifier}")

    index = identifier.indices[0][0]
    if not isinstance(index, ast.IntegerLiteral):
        raise ProgramConversionError(f"Expected integer index, got: {index}")

    return index.value


def _declaration_size(size: ast.Expression | None) -> int:
    """Return register size, defaulting scalar declarations to size one."""
    if size is None:
        return 1
    if not isinstance(size, ast.IntegerLiteral):
        raise ProgramConversionError(f"Expected integer register size, got: {size}")
    return size.value


def _argument_value(argument: ast.Expression) -> float:
    """Return a numeric gate argument after pyqasm validation and unrolling."""
    value = getattr(argument, "value", None)
    if not isinstance(value, (int, float)):
        raise ProgramConversionError(f"Expected numeric gate argument, got: {argument}")
    return float(value)


@weight(1.0)  # pylint: disable-next=too-many-locals,too-many-branches
def openqasm3_to_pyquil(program: QasmStringType | ast.Program) -> Program:
    """Returns a pyQuil Program equivalent to the input OpenQASM 3 AST program.

    Args:
        program: OpenQASM 3 AST program or string to convert.

    Returns:
        pyQuil Program representation equivalent to the input OpenQASM 3 program.
    """
    try:
        module = pyqasm.loads(program)
        module.validate()
    except Exception as err:
        raise ProgramConversionError("QASM program is not well-formed.") from err

    module.unroll()
    qasm_program = module.unrolled_ast
    quil_program = pyquil.Program()

    qubit_offsets: dict[str, int] = {}
    memory_regions: dict[str, object] = {}
    next_qubit = 0

    def qubit_index(qubit: ast.IndexedIdentifier) -> int:
        register = qubit.name.name
        if register not in qubit_offsets:
            raise ProgramConversionError(f"Undeclared qubit register: {register}")
        return qubit_offsets[register] + _index_value(qubit)

    def memory_reference(target: ast.IndexedIdentifier):
        register = target.name.name
        if register not in memory_regions:
            raise ProgramConversionError(f"Undeclared classical register: {register}")
        return memory_regions[register][_index_value(target)]

    def add_gate(name: str, arguments: list[float], qubits: list[int]) -> None:
        nonlocal quil_program

        lower_name = name.lower()
        gate_map = {
            "i": pyquil.gates.I,
            "id": pyquil.gates.I,
            "iden": pyquil.gates.I,
            "x": pyquil.gates.X,
            "y": pyquil.gates.Y,
            "z": pyquil.gates.Z,
            "h": pyquil.gates.H,
            "s": pyquil.gates.S,
            "t": pyquil.gates.T,
        }
        param_gate_map = {
            "rx": pyquil.gates.RX,
            "ry": pyquil.gates.RY,
            "rz": pyquil.gates.RZ,
            "p": pyquil.gates.PHASE,
            "phase": pyquil.gates.PHASE,
        }
        two_qubit_gate_map = {
            "cx": pyquil.gates.CNOT,
            "cnot": pyquil.gates.CNOT,
            "cz": pyquil.gates.CZ,
            "swap": pyquil.gates.SWAP,
        }

        if lower_name in gate_map and len(arguments) == 0 and len(qubits) == 1:
            quil_program += gate_map[lower_name](qubits[0])
        elif lower_name == "sdg" and len(arguments) == 0 and len(qubits) == 1:
            quil_program += pyquil.gates.PHASE(-math.pi / 2, qubits[0])
        elif lower_name == "tdg" and len(arguments) == 0 and len(qubits) == 1:
            quil_program += pyquil.gates.PHASE(-math.pi / 4, qubits[0])
        elif lower_name == "sx" and len(arguments) == 0 and len(qubits) == 1:
            quil_program += pyquil.gates.RX(math.pi / 2, qubits[0])
        elif lower_name in param_gate_map and len(arguments) == 1 and len(qubits) == 1:
            quil_program += param_gate_map[lower_name](arguments[0], qubits[0])
        elif lower_name in two_qubit_gate_map and len(arguments) == 0 and len(qubits) == 2:
            quil_program += two_qubit_gate_map[lower_name](*qubits)
        elif lower_name == "cp" and len(arguments) == 1 and len(qubits) == 2:
            quil_program += pyquil.gates.CPHASE(arguments[0], *qubits)
        elif lower_name == "ccx" and len(arguments) == 0 and len(qubits) == 3:
            quil_program += pyquil.gates.CCNOT(*qubits)
        elif lower_name == "cswap" and len(arguments) == 0 and len(qubits) == 3:
            quil_program += pyquil.gates.CSWAP(*qubits)
        elif lower_name == "rzz" and len(arguments) == 1 and len(qubits) == 2:
            quil_program += pyquil.gates.RZZ(arguments[0], *qubits)
        else:
            raise ProgramConversionError(f"Unsupported gate: {name}")

    for statement in qasm_program.statements:
        if isinstance(statement, ast.Include):
            if statement.filename not in {"stdgates.inc", "qelib1.inc"}:
                raise ProgramConversionError(f"Custom includes are unsupported: {statement}")
        elif isinstance(statement, ast.QubitDeclaration):
            qubit_offsets[statement.qubit.name] = next_qubit
            next_qubit += _declaration_size(statement.size)
        elif isinstance(statement, ast.ClassicalDeclaration):
            if not isinstance(statement.type, ast.BitType):
                raise ProgramConversionError(f"Unsupported classical declaration: {statement}")
            size = _declaration_size(statement.type.size)
            memory_regions[statement.identifier.name] = quil_program.declare(
                statement.identifier.name, "BIT", size
            )
            if isinstance(statement.init_expression, ast.QuantumMeasurement):
                quil_program += pyquil.gates.MEASURE(
                    qubit_index(statement.init_expression.qubit),
                    memory_regions[statement.identifier.name][0],
                )
            elif statement.init_expression is not None:
                raise ProgramConversionError(f"Unsupported classical initializer: {statement}")
        elif isinstance(statement, ast.QuantumMeasurementStatement):
            qubit = qubit_index(statement.measure.qubit)
            target = memory_reference(statement.target) if statement.target is not None else None
            quil_program += pyquil.gates.MEASURE(qubit, target)
        elif isinstance(statement, ast.QuantumGate):
            if statement.modifiers:
                raise ProgramConversionError(f"Unsupported gate modifiers: {statement.modifiers}")
            arguments = [_argument_value(argument) for argument in statement.arguments]
            qubits = [qubit_index(qubit) for qubit in statement.qubits]
            add_gate(statement.name.name, arguments, qubits)
        else:
            raise ProgramConversionError(f"Unsupported statement: {statement}")

    return quil_program

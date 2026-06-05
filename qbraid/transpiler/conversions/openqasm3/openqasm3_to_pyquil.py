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
Module defining OpenQASM 3 to pyQuil conversion function.

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
pyquil_gates = LazyLoader("pyquil_gates", globals(), "pyquil.gates")
pyquil_quilbase = LazyLoader("pyquil_quilbase", globals(), "pyquil.quilbase")

if TYPE_CHECKING:
    from pyquil import Program

    from qbraid.programs.typer import QasmStringType

# OpenQASM 3 delay time units -> seconds (pyQuil's DELAY duration is in seconds).
# "dt" is backend-dependent and has no fixed conversion, so it is unsupported.
_TIME_UNIT_SECONDS = {"ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1.0}

# OpenQASM gate name -> pyQuil gate constructor name. pyQuil's signature is
# uniform: fn(*params, *qubits), so a single dispatch handles every entry.
_GATE_MAP = {
    # one-qubit, no parameters
    "i": "I",
    "id": "I",
    "x": "X",
    "y": "Y",
    "z": "Z",
    "h": "H",
    "s": "S",
    "t": "T",
    # one-qubit, parameterized
    "rx": "RX",
    "ry": "RY",
    "rz": "RZ",
    "p": "PHASE",
    "phase": "PHASE",
    # two-qubit, no parameters
    "cx": "CNOT",
    "cnot": "CNOT",
    "cz": "CZ",
    "swap": "SWAP",
    "iswap": "ISWAP",
    # two-qubit, parameterized
    "cp": "CPHASE",
    "cphase": "CPHASE",
    "rxx": "RXX",
    "ryy": "RYY",
    "rzz": "RZZ",
    "xy": "XY",
    # three-qubit
    "ccx": "CCNOT",
    "toffoli": "CCNOT",
    "cswap": "CSWAP",
}


def _flat_qubit(qubit: ast.IndexedIdentifier | ast.Identifier, offsets: dict[str, int]) -> int:
    """Map an (unrolled) qubit reference to a flat pyQuil integer index."""
    if isinstance(qubit, ast.IndexedIdentifier):
        return offsets[qubit.name.name] + qubit.indices[0][0].value
    # bare Identifier => single-qubit register
    return offsets[qubit.name]


def _duration_seconds(duration: ast.DurationLiteral) -> float:
    """Convert an OpenQASM 3 delay duration to seconds for pyQuil's DELAY."""
    unit = duration.unit.name
    if unit not in _TIME_UNIT_SECONDS:
        raise ProgramConversionError(f"Unsupported delay unit: {unit}")
    return duration.value * _TIME_UNIT_SECONDS[unit]


def _literal_bit(node: ast.Expression) -> int:
    """Read a 0/1 from the literal side of a branch comparison."""
    if isinstance(node, ast.BooleanLiteral):
        return 1 if node.value else 0
    if isinstance(node, ast.IntegerLiteral) and node.value in (0, 1):
        return node.value
    raise ProgramConversionError("Unsupported branch comparison value (expected 0 or 1).")


@weight(1.0)  # pylint: disable-next=too-many-statements
def openqasm3_to_pyquil(program: QasmStringType | ast.Program) -> Program:
    """Returns a pyQuil Program equivalent to the input OpenQASM 3 program.

    Supports the standard gate set (including gate modifiers and controlled gates,
    which ``pyqasm`` decomposes during unrolling), measurement, ``barrier`` (-> pyQuil
    ``FENCE``), ``reset`` (-> ``RESET``), ``delay`` (-> ``DELAY``), and ``if (c == 0|1)``
    classical feedforward (-> conditional ``JUMP-WHEN``). Declared-but-idle qubits are
    padded with identity so the operator dimension matches the source register width.

    Args:
        program (str or openqasm3.ast.Program): OpenQASM 3 program to convert.

    Returns:
        pyquil.Program: pyQuil Program equivalent to the input program.

    Raises:
        ProgramConversionError: If the program is malformed or contains a
            gate/statement that is not supported by the conversion.
    """
    try:
        module = pyqasm.loads(program)
        module.validate()
    except Exception as e:
        raise ProgramConversionError("QASM program is not well-formed.") from e

    module.unroll()
    unrolled = module.unrolled_ast

    quil = pyquil.Program()

    # pass 1: build flat qubit + classical-bit offset maps
    qubit_offsets: dict[str, int] = {}
    clbit_offsets: dict[str, int] = {}
    num_qubits = 0
    num_clbits = 0
    for statement in unrolled.statements:
        if isinstance(statement, ast.QubitDeclaration):
            size = statement.size.value if statement.size is not None else 1
            qubit_offsets[statement.qubit.name] = num_qubits
            num_qubits += size
        elif isinstance(statement, ast.ClassicalDeclaration) and isinstance(
            statement.type, ast.BitType
        ):
            size = statement.type.size.value if statement.type.size is not None else 1
            clbit_offsets[statement.identifier.name] = num_clbits
            num_clbits += size

    ro = quil.declare("ro", "BIT", num_clbits) if num_clbits else None

    # track which declared qubits are acted on, so idle ones can be padded with I
    # (keeps the operator dimension equal to the declared register width)
    used_qubits: set[int] = set()

    def flat(qubit: ast.IndexedIdentifier | ast.Identifier) -> int:
        index = _flat_qubit(qubit, qubit_offsets)
        used_qubits.add(index)
        return index

    def branch_target(condition: ast.Expression) -> tuple[object, int]:
        """Resolve a branch condition ``c[i] == 0|1`` to (memory_ref, expected_bit)."""
        if not isinstance(condition, ast.BinaryExpression) or condition.op.name != "==":
            raise ProgramConversionError("Unsupported branch condition (expected '==').")
        lhs, rhs = condition.lhs, condition.rhs
        if isinstance(lhs, (ast.BooleanLiteral, ast.IntegerLiteral)):
            lhs, rhs = rhs, lhs
        if not isinstance(lhs, ast.IndexExpression) or ro is None:
            raise ProgramConversionError("Unsupported branch condition target.")
        name = lhs.collection.name
        if name not in clbit_offsets:
            raise ProgramConversionError(f"Unknown classical register in branch: {name}")
        ro_index = clbit_offsets[name] + lhs.index[0].value
        return ro[ro_index], _literal_bit(rhs)

    def emit(statement: ast.Statement, prog: Program) -> None:
        # statements with no observable pyQuil equivalent that are safe to drop:
        #   QuantumPhase = global phase (gphase), unobservable (pyqasm emits it when
        #   decomposing gates such as rzz; equivalence holds up to global phase).
        if isinstance(
            statement,
            (ast.QubitDeclaration, ast.ClassicalDeclaration, ast.Include, ast.QuantumPhase),
        ):
            return

        if isinstance(statement, ast.QuantumBarrier):
            prog.inst(pyquil_quilbase.Fence([flat(q) for q in statement.qubits]))

        elif isinstance(statement, ast.QuantumReset):
            prog.inst(pyquil_gates.RESET(flat(statement.qubits)))

        elif isinstance(statement, ast.DelayInstruction):
            qubits = [flat(q) for q in statement.qubits]
            prog.inst(pyquil_quilbase.DelayQubits(qubits, _duration_seconds(statement.duration)))

        elif isinstance(statement, ast.QuantumGate):
            name = statement.name.name.lower()
            if statement.modifiers:
                raise ProgramConversionError(f"Unsupported gate modifier on: {name}")
            params = [arg.value for arg in statement.arguments]
            qubits = [flat(q) for q in statement.qubits]

            if name == "sdg":
                prog.inst(pyquil_gates.S(*qubits).dagger())
            elif name == "tdg":
                prog.inst(pyquil_gates.T(*qubits).dagger())
            elif name == "sx":
                prog.inst(pyquil_gates.RX(math.pi / 2, *qubits))
            elif name == "sxdg":
                prog.inst(pyquil_gates.RX(-math.pi / 2, *qubits))
            elif name in ("u", "u3"):
                prog.inst(pyquil_gates.U(*params, *qubits))
            elif name in _GATE_MAP:
                prog.inst(getattr(pyquil_gates, _GATE_MAP[name])(*params, *qubits))
            else:
                raise ProgramConversionError(f"Unsupported gate: {name}")

        elif isinstance(statement, ast.QuantumMeasurementStatement):
            src = flat(statement.measure.qubit)
            if statement.target is not None and ro is not None:
                target = statement.target
                ro_index = clbit_offsets[target.name.name] + target.indices[0][0].value
                prog.inst(pyquil_gates.MEASURE(src, ro[ro_index]))
            else:
                prog.inst(pyquil_gates.MEASURE(src, None))

        elif isinstance(statement, ast.BranchingStatement):
            # classical feedforward: if (c[i] == 1) { ... } else { ... } -> JUMP-WHEN
            reg, expected = branch_target(statement.condition)
            then_block, else_block = statement.if_block, statement.else_block
            if expected == 0:  # run the if-body when the bit is 0 => swap into the else slot
                then_block, else_block = else_block, then_block
            then_prog = pyquil.Program()
            for inner in then_block:
                emit(inner, then_prog)
            else_prog = pyquil.Program()
            for inner in else_block:
                emit(inner, else_prog)
            prog.if_then(reg, then_prog, else_prog if else_block else None)

        else:
            raise ProgramConversionError(f"Unsupported statement: {statement}")

    for statement in unrolled.statements:
        emit(statement, quil)

    # pad idle declared qubits with identity so the operator spans the full register
    for index in range(num_qubits):
        if index not in used_qubits:
            quil += pyquil_gates.I(index)

    return quil

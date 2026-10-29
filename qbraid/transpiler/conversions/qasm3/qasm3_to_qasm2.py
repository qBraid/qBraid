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
Module containing OpenQASM 3 to OpenQASM 2 conversion function

"""
from __future__ import annotations

import re

import pyqasm
from openqasm3 import ast
from openqasm3.visitor import QASMVisitor

from qbraid.programs.typer import Qasm2StringType, Qasm3StringType
from qbraid.transpiler.annotations import weight

# The original qelib1.inc gates, plus the extended ones the Cirq-based conversion
# already emits. These are kept as written and every other gate is unrolled into them,
# so a gate that is neither raises and the transpiler takes the Cirq path.
QELIB1_GATES = frozenset(
    {
        "u3", "u2", "u1", "cx", "id", "x", "y", "z", "h", "s", "sdg", "t", "tdg", "rx", "ry",
        "rz", "cz", "cy", "ch", "ccx", "crz", "cu1", "cu3", "sx", "sxdg", "p", "swap", "cswap",
    }
)  # fmt: skip

# Names qelib1.inc defines (including its extended gates) or QASM 2 keeps as keywords; a
# register with one of these names would not parse.
_RESERVED_NAMES = QELIB1_GATES | {
    "u", "cp", "crx", "cry", "cu", "csx", "rxx", "rzz", "rccx", "rc3x", "c3x", "c3sqrtx", "c4x",
    "u0", "opaque", "sin", "cos", "tan", "exp", "ln", "sqrt",
}  # fmt: skip
_QASM2_IDENTIFIER = re.compile(r"[a-z][A-Za-z0-9_]*")

_DECLARATION = re.compile(r"^(qubit|bit)\[(\d+)\] (\w+);$")
_MEASUREMENT = re.compile(r"^(\w+\[\d+\]) = measure (\w+\[\d+\]);$")
_UNTARGETED_MEASUREMENT = re.compile(r"^measure (\w+\[\d+\]);$")
_GATE = re.compile(r"^(\w+)(?:\([^)]*\))? [^;]+;$")
_BOX = re.compile(r"^box(?:\[[^\]]*\])? \{$")
_GATE_DEFINITION = re.compile(r"\bgate\s+(\w+)")
_EXPONENT_WITHOUT_POINT = re.compile(r"(?<![\w.])(\d+)([eE][-+]?\d+)")


@weight(1)
def qasm3_to_qasm2(qasm: Qasm3StringType) -> Qasm2StringType:
    """Convert an OpenQASM 3 program to OpenQASM 2, keeping every classical register whole.

    Each ``bit[n] c`` becomes ``creg c[n]`` under its own name, with unmeasured bits left in
    place, so a backend that counts each register separately keeps the correlations
    between its bits.

    A measurement with no target bit gets the next bit of an added ``m_m`` register, the
    name the Cirq path gives it.

    Raises:
        ValueError: If the program has a statement OpenQASM 2 cannot express, such as a
            classical write to a bit, a condition on a single bit, a physical qubit
            (``$1``), or a register name OpenQASM 2 cannot use. The transpiler then tries
            its next conversion path.
    """
    # Unrolling drops a write such as ``c[1] = 1;`` without a trace, and the whole
    # register would then report that bit as 0.
    program = pyqasm.loads(qasm).original_program
    bit_writes = _BitWriteFinder()
    bit_writes.visit(program)
    if bit_writes.found:
        raise ValueError("OpenQASM 2 cannot express a classical write to a bit.")
    # pyqasm unrolls ``cx a, b`` over two registers as ``cx a[0], a[1]; cx b[0], b[1];``
    # (qBraid/pyqasm#384); the Cirq path broadcasts it correctly.
    broadcasts = _BroadcastFinder()
    broadcasts.visit(program)
    if broadcasts.found:
        raise ValueError("Cannot unroll a multi-qubit gate broadcast over a register.")

    unrolled = _unroll(qasm)
    if "$" in unrolled:
        raise ValueError("OpenQASM 2 cannot express a physical qubit.")

    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";']
    untargeted = _untargeted_register(unrolled)
    untargeted_bits = declaration_at = open_boxes = 0
    for statement in unrolled.splitlines():
        statement = statement.strip()
        if not statement or statement.startswith(("OPENQASM", "include")):
            continue
        if declaration := _DECLARATION.match(statement):
            kind, size, name = declaration.groups()
            if not _QASM2_IDENTIFIER.fullmatch(name) or name in _RESERVED_NAMES:
                raise ValueError(f"OpenQASM 2 cannot name a register {name!r}.")
            lines.append(f"{'qreg' if kind == 'qubit' else 'creg'} {name}[{size}];")
        elif measurement := _MEASUREMENT.match(statement):
            clbit, qubit = measurement.groups()
            lines.append(f"measure {qubit} -> {clbit};")
        elif measurement := _UNTARGETED_MEASUREMENT.match(statement):
            if not untargeted_bits:
                declaration_at = len(lines)
            lines.append(f"measure {measurement.group(1)} -> {untargeted}[{untargeted_bits}];")
            untargeted_bits += 1
        elif _BOX.match(statement):
            open_boxes += 1  # A box only schedules its body, so the body is kept as is.
        elif statement == "}" and open_boxes:
            open_boxes -= 1
        elif statement.startswith(("reset ", "barrier ")):
            lines.append(statement)
        elif statement.startswith("gphase"):
            continue  # A global phase has no observable effect.
        elif (gate := _GATE.match(statement)) and gate.group(1) in QELIB1_GATES:
            # OpenQASM 2 requires a decimal point in a real literal, as in 1.0e-05.
            lines.append(_EXPONENT_WITHOUT_POINT.sub(r"\1.0\2", statement))
        else:
            raise ValueError(f"OpenQASM 2 cannot express the statement: {statement}")

    if untargeted_bits:
        lines.insert(declaration_at, f"creg {untargeted}[{untargeted_bits}];")
    return "\n".join(lines) + "\n"


def _untargeted_register(unrolled: str) -> str:
    """A register name for measurements with no target that no declaration already uses."""
    declared = {match.group(3) for match in map(_DECLARATION.match, unrolled.splitlines()) if match}
    name, suffix = "m_m", 0
    while name in declared:
        suffix += 1
        name = f"m_m{suffix}"
    return name


class _BitWriteFinder(QASMVisitor):
    """Records whether a program assigns to a bit, including in a declaration."""

    def __init__(self):
        self.bits: set[str] = set()
        self.found = False

    # pylint: disable-next=invalid-name,unused-argument
    def visit_ClassicalDeclaration(self, node: ast.ClassicalDeclaration, context=None) -> None:
        """Track bit declarations and flag one that sets an initial value."""
        if isinstance(node.type, ast.BitType):
            self.bits.add(node.identifier.name)
            self.found |= node.init_expression is not None

    # pylint: disable-next=invalid-name,unused-argument
    def visit_ClassicalAssignment(self, node: ast.ClassicalAssignment, context=None) -> None:
        """Flag an assignment whose target is a declared bit."""
        target = node.lvalue.name
        name = target.name if isinstance(target, ast.Identifier) else target
        self.found |= name in self.bits


class _BroadcastFinder(QASMVisitor):
    """Records whether a gate on two or more operands broadcasts over a register."""

    def __init__(self):
        self.registers: set[str] = set()
        self.found = False

    # pylint: disable-next=invalid-name,unused-argument
    def visit_QubitDeclaration(self, node: ast.QubitDeclaration, context=None) -> None:
        """Track qubit registers, which a bare name broadcasts over."""
        if node.size is not None:
            self.registers.add(node.qubit.name)

    # pylint: disable-next=invalid-name,unused-argument
    def visit_AliasStatement(self, node: ast.AliasStatement, context=None) -> None:
        """Treat an alias as a register, since it may name several qubits."""
        self.registers.add(node.target.name)

    # pylint: disable-next=invalid-name,unused-argument
    def visit_QuantumArgument(self, node: ast.QuantumArgument, context=None) -> None:
        """Track a subroutine's register arguments."""
        if node.size is not None:
            self.registers.add(node.name.name)

    # pylint: disable-next=invalid-name,unused-argument
    def visit_QuantumGateDefinition(self, node: ast.QuantumGateDefinition, context=None) -> None:
        """Skip gate bodies, whose operands are always single qubits."""

    # pylint: disable-next=invalid-name,unused-argument
    def visit_QuantumGate(self, node: ast.QuantumGate, context=None) -> None:
        """Flag a gate on two or more operands where one names several qubits."""
        if len(node.qubits) > 1:
            self.found |= any(self._is_register(operand) for operand in node.qubits)

    def _is_register(self, operand: ast.Expression) -> bool:
        if isinstance(operand, ast.Identifier):
            return operand.name in self.registers
        if isinstance(operand, ast.IndexedIdentifier):
            return any(
                isinstance(index, (ast.RangeDefinition, ast.DiscreteSet))
                for indices in operand.indices
                for index in (indices if isinstance(indices, list) else [indices])
            )
        return False


def _unroll(qasm: str) -> str:
    """``qasm`` unrolled into gates, keeping qelib1 gates as written where that is safe.

    A gate the program defines itself under a qelib1 name is unrolled, since QASM 2 would
    run qelib1's gate instead. If a modifier (``ctrl @``, ``inv @``) is left on a kept gate,
    everything is unrolled instead, which QASM 2 can express.
    """
    module = pyqasm.loads(qasm)
    module.unroll(external_gates=sorted(QELIB1_GATES - set(_GATE_DEFINITION.findall(qasm))))
    unrolled = pyqasm.dumps(module)
    if "@" not in unrolled:
        return unrolled
    module = pyqasm.loads(qasm)
    module.unroll()
    return pyqasm.dumps(module)

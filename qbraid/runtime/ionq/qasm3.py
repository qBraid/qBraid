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
Module that prepares OpenQASM 3 programs for IonQ's ``ionq.qasm3.v1`` job type.

IonQ accepts a subset of OpenQASM 3. See https://docs.ionq.com/api-reference/v0.4/openqasm3.

"""

from __future__ import annotations

import math
import re

import openqasm3
import pyqasm
from openqasm3 import ast
from openqasm3.visitor import QASMVisitor
from pyqasm.elements import BasisSet

from qbraid._logging import logger
from qbraid.transpiler import ProgramConversionError

#: Gates IonQ accepts in an OpenQASM 3 program, including IonQ's aliases.
IONQ_QASM3_GATES = frozenset(
    {
        "x",
        "not",
        "y",
        "z",
        "h",
        "s",
        "sdg",
        "si",
        "t",
        "tdg",
        "ti",
        "sx",
        "v",
        "vdg",
        "vi",
        "rx",
        "ry",
        "rz",
        "p",
        "id",
        "xphase",
        "yphase",
        "gphase",
        "cx",
        "cnot",
        "cy",
        "cz",
        "swap",
    }
)

#: Gates IonQ lets ``ctrl @`` act on. Only a single control is safe to send.
IONQ_QASM3_CONTROLLABLE_GATES = frozenset({"x", "not", "z", "rz", "xphase", "yphase"})

# Toffoli as h, t, tdg and cx: the standard six-CNOT decomposition, with no phase difference.
_CCX_DECOMPOSITION = (
    "h {c}; cx {b}, {c}; tdg {c}; cx {a}, {c}; t {c}; cx {b}, {c}; tdg {c}; cx {a}, {c}; "
    "t {b}; t {c}; h {c}; cx {a}, {b}; t {a}; tdg {b}; cx {a}, {b};"
)
_CCX_LINE = re.compile(r"^(\s*)ccx\s+([^,;]+),\s*([^,;]+),\s*([^,;]+);\s*$", re.MULTILINE)
_ROTATION_LINE = re.compile(r"^(\s*)(rx|ry|rz|p)\(([^()]*)\)(\s+[^;]+;)\s*$", re.MULTILINE)


class _UnsupportedFinder(QASMVisitor[None]):
    """Collects the constructs in a program that IonQ rejects or runs incorrectly."""

    def __init__(self) -> None:
        self.defined_gates: set[str] = set()
        self.problems: list[str] = []

    def _add(self, problem: str) -> None:
        if problem not in self.problems:
            self.problems.append(problem)

    def visit_QuantumGateDefinition(self, node: ast.QuantumGateDefinition) -> None:
        """Record a program-defined gate, then check its body."""
        self.defined_gates.add(node.name.name)
        self.generic_visit(node)

    def visit_QuantumGate(self, node: ast.QuantumGate) -> None:
        """Check a gate call and its modifiers."""
        name = node.name.name
        if node.modifiers:
            if len(node.modifiers) > 1:
                self._add(f"more than one modifier on '{name}'")
                return
            modifier = node.modifiers[0]
            if modifier.modifier != ast.GateModifierName.ctrl:
                self._add(f"'{modifier.modifier.name} @' modifier")
                return
            controls = modifier.argument
            num_controls = (
                1
                if controls is None
                else controls.value if isinstance(controls, ast.IntegerLiteral) else None
            )
            if num_controls != 1:
                self._add(f"'ctrl({num_controls if num_controls else '...'}) @ {name}'")
            elif name not in IONQ_QASM3_CONTROLLABLE_GATES:
                self._add(f"'ctrl @ {name}'")
            return
        if name not in IONQ_QASM3_GATES and name not in self.defined_gates:
            self._add(f"gate '{name}'")

    def visit_QuantumMeasurementStatement(self, node: ast.QuantumMeasurementStatement) -> None:
        """Check that a measurement reads one qubit into one bit."""
        if not isinstance(node.measure.qubit, ast.IndexedIdentifier):
            self._add("whole-register measurement")
        elif node.target is None:
            self._add("measurement without a target bit")

    def visit_QuantumReset(self, node: ast.QuantumReset) -> None:
        """Check that a reset acts on one qubit."""
        if not isinstance(node.qubits, ast.IndexedIdentifier):
            self._add("whole-register reset")

    def visit_ForInLoop(self, _node: ast.ForInLoop) -> None:
        """IonQ does not support for loops, so the program is unrolled."""
        self._add("for loop")


def find_unsupported(qasm: str) -> list[str]:
    """Return the constructs in ``qasm`` that IonQ rejects or does not run as written.

    Covers gates IonQ does not support (unless the program defines them), gate modifiers
    other than ``ctrl @`` with one control on a gate that allows it, whole-register
    measurements and resets, measurements without a target bit, and ``for`` loops.

    Args:
        qasm: An OpenQASM 3 program.

    Returns:
        A list of short descriptions, empty when the program needs no changes. A program
        that does not parse also returns an empty list, so it is sent as written and IonQ
        reports the error.
    """
    try:
        program = openqasm3.parse(qasm)
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.debug("Could not parse OpenQASM 3 program to check it for IonQ: %s", err)
        return []
    finder = _UnsupportedFinder()
    finder.visit(program)
    return finder.problems


def _expand_ccx(qasm: str) -> str:
    """Replace each ``ccx`` statement with gates IonQ supports."""

    def expand(match: re.Match) -> str:
        indent, a, b, c = match.group(1), *(operand.strip() for operand in match.groups()[1:])
        statements = _CCX_DECOMPOSITION.format(a=a, b=b, c=c).split("; ")
        return "\n".join(indent + statement.rstrip(";") + ";" for statement in statements)

    return _CCX_LINE.sub(expand, qasm)


def _normalize_angles(qasm: str) -> str:
    """Write each ``rx``, ``ry``, ``rz`` and ``p`` angle as a value in [0, 2π).

    IonQ documents that gate arguments may not contain ``+`` or ``-``. For these
    uncontrolled gates a shift by 2π changes at most the global phase.
    """

    def normalize(match: re.Match) -> str:
        indent, gate, angle, rest = match.groups()
        try:
            value = float(angle)
        except ValueError:
            return match.group(0)
        value = math.fmod(value, 2 * math.pi)
        if value < 0:
            value += 2 * math.pi
        if value >= 2 * math.pi:
            value = 0.0
        return f"{indent}{gate}({value!r}){rest}"

    return _ROTATION_LINE.sub(normalize, qasm)


def to_ionq_qasm3(qasm: str) -> str:
    """Rewrite an OpenQASM 3 program into the subset IonQ runs as written.

    The program is unrolled with pyqasm, which inlines gate definitions and loops and
    splits whole-register measurements and resets into one statement per qubit. Each
    ``ccx`` (including one unrolled from ``ctrl(2) @ x``) is replaced by ``h``, ``t``,
    ``tdg`` and ``cx`` gates. Any other unsupported gate left over is rebased to ``rx``,
    ``ry``, ``rz`` and ``cx``. Finally, rotation angles are written in [0, 2π).

    Args:
        qasm: An OpenQASM 3 program.

    Returns:
        The rewritten OpenQASM 3 program.

    Raises:
        ProgramConversionError: If the program cannot be rewritten into gates IonQ supports.
    """
    try:
        module = pyqasm.loads(qasm)
        module.unroll()
        rewritten = _expand_ccx(pyqasm.dumps(module))
        if find_unsupported(rewritten):
            module = pyqasm.loads(rewritten)
            module.rebase(BasisSet.ROTATIONAL_CX)
            rewritten = _expand_ccx(pyqasm.dumps(module))
    except Exception as err:
        raise ProgramConversionError(
            f"Could not rewrite the program into OpenQASM 3 that IonQ supports: {err}"
        ) from err

    rewritten = _normalize_angles(rewritten)
    if problems := find_unsupported(rewritten):
        raise ProgramConversionError(
            "Could not rewrite the program into OpenQASM 3 that IonQ supports. "
            f"Still unsupported: {', '.join(problems)}."
        )
    return rewritten

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
Module converting OpenQASM 3 into the OpenQASM 2 that OQC compiles.

"""
from __future__ import annotations

import re

import openqasm3
import pyqasm
from openqasm3.visitor import QASMVisitor

# The original qelib1.inc gates, plus the extended ones OQC's parser also resolves.
QELIB1_GATES = frozenset(
    {
        "u3", "u2", "u1", "cx", "id", "x", "y", "z", "h", "s", "sdg", "t", "tdg", "rx", "ry",
        "rz", "cz", "cy", "ch", "ccx", "crz", "cu1", "cu3", "sx", "sxdg", "p", "u", "swap",
        "cp", "crx", "cry", "cswap", "rxx", "rzz", "csx", "cu", "rccx",
    }
)  # fmt: skip

_DECLARATION = re.compile(r"^(qubit|bit)\[(\d+)\] (\w+);$")
_MEASUREMENT = re.compile(r"^(\w+\[\d+\]) = measure (\w+\[\d+\]);$")
_GATE = re.compile(r"^(\w+)(?:\([^)]*\))? [^;]+;$")
_EXPONENT_WITHOUT_POINT = re.compile(r"(?<![\w.])(\d+)([eE][-+]?\d+)")


class _PhysicalQubitFinder(QASMVisitor):
    """Records whether any identifier names a physical qubit."""

    def __init__(self):
        self.found = False

    def visit_Identifier(self, node, context=None):  # pylint: disable=invalid-name,unused-argument
        """Physical qubits are identifiers spelled ``$n``."""
        self.found = self.found or node.name.startswith("$")


def uses_physical_qubits(qasm: str) -> bool:
    """Return whether an OpenQASM 3 program addresses physical qubits, such as ``$1``."""
    finder = _PhysicalQubitFinder()
    finder.visit(openqasm3.parse(qasm))
    return finder.found


def qasm3_to_qasm2(qasm: str) -> str:
    """Convert an OpenQASM 3 program to OpenQASM 2, keeping every classical register whole.

    Each ``bit[n] c`` becomes ``creg c[n]`` under its own name, with unmeasured bits left in
    place, so OQC reports it as one register. OQC returns a separate histogram per register,
    so splitting a register would discard the correlations between its bits.

    Raises:
        ValueError: If the unrolled program has a statement OpenQASM 2 cannot express, such
            as a condition on a single bit, a measurement with no target, or a physical
            qubit (``$1``).
    """
    module = pyqasm.loads(qasm)
    module.unroll()
    unrolled = pyqasm.dumps(module)
    if "$" in unrolled:
        raise ValueError("OpenQASM 2 cannot express a physical qubit.")

    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";']
    for statement in unrolled.splitlines():
        statement = statement.strip()
        if not statement or statement.startswith(("OPENQASM", "include")):
            continue
        if declaration := _DECLARATION.match(statement):
            kind, size, name = declaration.groups()
            lines.append(f"{'qreg' if kind == 'qubit' else 'creg'} {name}[{size}];")
        elif measurement := _MEASUREMENT.match(statement):
            clbit, qubit = measurement.groups()
            lines.append(f"measure {qubit} -> {clbit};")
        elif statement.startswith(("reset ", "barrier ")):
            lines.append(statement)
        elif statement.startswith("gphase"):
            continue  # A global phase has no observable effect.
        elif (gate := _GATE.match(statement)) and gate.group(1) in QELIB1_GATES:
            # OpenQASM 2 requires a decimal point in a real literal, as in 1.0e-05.
            lines.append(_EXPONENT_WITHOUT_POINT.sub(r"\1.0\2", statement))
        else:
            raise ValueError(f"OpenQASM 2 cannot express the statement: {statement}")

    return "\n".join(lines) + "\n"

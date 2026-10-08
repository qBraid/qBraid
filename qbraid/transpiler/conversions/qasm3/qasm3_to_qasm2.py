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
from pyqasm.elements import BasisSet

from qbraid.programs.typer import Qasm2StringType, Qasm3StringType
from qbraid.transpiler.annotations import weight

# The original qelib1.inc gates, plus the extended ones the Cirq-based conversion
# already emits. Any other gate is rebased onto rx, ry, rz and cx.
QELIB1_GATES = frozenset(
    {
        "u3", "u2", "u1", "cx", "id", "x", "y", "z", "h", "s", "sdg", "t", "tdg", "rx", "ry",
        "rz", "cz", "cy", "ch", "ccx", "crz", "cu1", "cu3", "sx", "sxdg", "p", "swap", "cswap",
    }
)  # fmt: skip

# Names qelib1.inc defines (including its extended gates) or QASM 2 reserves; a register
# with one of these names would not parse.
_RESERVED_NAMES = QELIB1_GATES | {
    "u", "cp", "crx", "cry", "cu", "csx", "rxx", "rzz", "rccx", "rc3x", "c3x", "c3sqrtx", "c4x",
    "u0", "opaque",
}  # fmt: skip
_QASM2_IDENTIFIER = re.compile(r"[a-z][A-Za-z0-9_]*")

_DECLARATION = re.compile(r"^(qubit|bit)\[(\d+)\] (\w+);$")
_MEASUREMENT = re.compile(r"^(\w+\[\d+\]) = measure (\w+\[\d+\]);$")
_GATE = re.compile(r"^(\w+)(?:\([^)]*\))? [^;]+;$")
_EXPONENT_WITHOUT_POINT = re.compile(r"(?<![\w.])(\d+)([eE][-+]?\d+)")


def _gate_names(qasm: str) -> set[str]:
    return {match.group(1) for line in qasm.splitlines() if (match := _GATE.match(line.strip()))}


@weight(1)
def qasm3_to_qasm2(qasm: Qasm3StringType) -> Qasm2StringType:
    """Convert an OpenQASM 3 program to OpenQASM 2, keeping every classical register whole.

    Each ``bit[n] c`` becomes ``creg c[n]`` under its own name, with unmeasured bits left in
    place, so a backend that counts each register separately keeps the correlations
    between its bits.

    Raises:
        ValueError: If the unrolled program has a statement OpenQASM 2 cannot express, such
            as a condition on a single bit, a measurement with no target, a physical qubit
            (``$1``), or a register name OpenQASM 2 cannot use. The transpiler then tries
            its next conversion path.
    """
    module = pyqasm.loads(qasm)
    module.unroll()
    unrolled = pyqasm.dumps(module)
    if "$" in unrolled:
        raise ValueError("OpenQASM 2 cannot express a physical qubit.")
    if _gate_names(unrolled) - QELIB1_GATES - {"OPENQASM", "include", "reset", "barrier", "gphase"}:
        module.rebase(BasisSet.ROTATIONAL_CX)
        unrolled = pyqasm.dumps(module)

    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";']
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

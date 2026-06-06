# Copyright 2026 qBraid
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

"""Function for converting an OpenQASM 3 string to a Qibo circuit."""

# pylint: disable=import-outside-toplevel,eval-used

from __future__ import annotations

import ast
import math
import re
from typing import TYPE_CHECKING

from qbraid.transpiler.exceptions import ProgramConversionError

if TYPE_CHECKING:
    import qibo.models

_QUBIT_DECL = re.compile(r"qubit\[(\d+)\]\s+(\w+)\s*;")
_MEASURE = re.compile(r"measure\s+(\w+)\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]\s*;")
_PARAM_GATE = re.compile(r"(\w+)\s*\(([^)]+)\)\s+([\w\[\], ]+)\s*;")
_FIXED_GATE = re.compile(r"(\w+)\s+([\w\[\], ]+)\s*;")
_QUBIT_INDEX = re.compile(r"\w+\[(\d+)\]")

_SKIP_PREFIXES = ("openqasm", "include", "qubit", "bit", "//", "#")


def _parse_param(expr: str) -> float:
    """Safely evaluate a QASM3 numeric expression (supports ``pi`` and basic arithmetic).

    Args:
        expr: Parameter expression string, e.g. ``"pi/2"`` or ``"1.5707963"``.

    Returns:
        Float value of the expression.

    Raises:
        ProgramConversionError: If the expression is malformed or uses unsafe constructs.
    """
    expr = expr.strip().replace("pi", str(math.pi))
    try:
        tree = ast.parse(expr, mode="eval")
        _allowed = (
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Constant,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.USub,
            ast.UAdd,
        )
        for node in ast.walk(tree):
            if not isinstance(node, _allowed):
                raise ValueError(f"Unsafe AST node: {type(node).__name__}")
        return float(eval(compile(tree, "<qasm3_param>", "eval")))  # noqa: S307
    except Exception as exc:
        raise ProgramConversionError(
            f"Cannot evaluate parameter expression '{expr}': {exc}"
        ) from exc


def _fixed_gate_map() -> dict:
    """Build lazy mapping from QASM3 gate names to Qibo gate constructors (no parameters)."""
    import qibo.gates as g  # noqa: PLC0415

    base = {
        "h": g.H,
        "x": g.X,
        "y": g.Y,
        "z": g.Z,
        "cx": g.CNOT,
        "cz": g.CZ,
        "swap": g.SWAP,
        "ccx": g.TOFFOLI,
    }
    for _attr, _key in [
        ("S", "s"),
        ("T", "t"),
        ("SDG", "sdg"),
        ("TDG", "tdg"),
        ("SX", "sx"),
        ("I", "id"),
        ("CY", "cy"),
        ("ECR", "ecr"),
        ("CSWAP", "cswap"),
    ]:
        if hasattr(g, _attr):
            base[_key] = getattr(g, _attr)
    for _attr in ("iSWAP", "ISWAP"):
        if hasattr(g, _attr):
            base.setdefault("iswap", getattr(g, _attr))
    return base


def _param_gate_map() -> dict:
    """Build lazy mapping from QASM3 gate names to Qibo gate constructors (with parameters)."""
    import qibo.gates as g  # noqa: PLC0415

    return {
        "rx": g.RX,
        "ry": g.RY,
        "rz": g.RZ,
        "p": g.U1,
        "u": g.U3,
        "crx": g.CRX,
        "cry": g.CRY,
        "crz": g.CRZ,
        "cp": g.CU1,
    }


def qasm3_to_qibo(qasm3_str: str) -> "qibo.models.Circuit":
    """Convert an OpenQASM 3 string to a :class:`qibo.models.Circuit`.

    Only programs using the standard ``stdgates.inc`` gate library are supported.
    Classical control flow (``if``, ``for``, ``while``) and inline gate definitions
    are not handled.

    Args:
        qasm3_str: OpenQASM 3 source string to convert.

    Returns:
        A :class:`qibo.models.Circuit` equivalent to the input program.

    Raises:
        ProgramConversionError: If the string cannot be parsed, the qubit count
            cannot be determined, or an unsupported gate is encountered.

    Example:
        >>> qasm = '''
        ... OPENQASM 3.0;
        ... include "stdgates.inc";
        ... qubit[2] q;
        ... h q[0];
        ... cx q[0], q[1];
        ... '''
        >>> circuit = qasm3_to_qibo(qasm)
        >>> circuit.nqubits
        2
        >>> len(circuit.queue)
        2
    """
    import qibo.models  # noqa: PLC0415

    fixed = _fixed_gate_map()
    parametric = _param_gate_map()

    # Count total qubits across all register declarations
    nqubits = sum(
        int(m.group(1))
        for line in qasm3_str.splitlines()
        for m in [_QUBIT_DECL.match(line.strip())]
        if m
    )
    if nqubits == 0:
        raise ProgramConversionError(
            "Could not determine qubit count from the QASM 3 string. "
            "Expected at least one 'qubit[N] name;' declaration."
        )

    circuit = qibo.models.Circuit(nqubits)

    for raw_line in qasm3_str.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(line.lower().startswith(p) for p in _SKIP_PREFIXES):
            continue

        # Measurement: measure reg[i] -> creg[j];
        m = _MEASURE.match(line)
        if m:
            import qibo.gates  # noqa: PLC0415

            qubit_idx = int(m.group(2))
            circuit.add(qibo.gates.M(qubit_idx))
            continue

        # Parametric gate: name(p1, p2, ...) q[i], q[j], ...;
        m = _PARAM_GATE.match(line)
        if m:
            gate_name = m.group(1).lower()
            params = [_parse_param(p) for p in m.group(2).split(",")]
            qubits = [int(q) for q in _QUBIT_INDEX.findall(m.group(3))]
            if gate_name not in parametric:
                raise ProgramConversionError(
                    f"Unsupported parametric gate '{gate_name}' in qasm3_to_qibo."
                )
            circuit.add(parametric[gate_name](*qubits, *params))
            continue

        # Fixed gate: name q[i], q[j], ...;
        m = _FIXED_GATE.match(line)
        if m:
            gate_name = m.group(1).lower()
            qubits = [int(q) for q in _QUBIT_INDEX.findall(m.group(2))]
            if gate_name not in fixed:
                raise ProgramConversionError(
                    f"Unsupported gate '{gate_name}' in qasm3_to_qibo. "
                    "Only stdgates.inc gates are currently supported."
                )
            circuit.add(fixed[gate_name](*qubits))
            continue

    return circuit

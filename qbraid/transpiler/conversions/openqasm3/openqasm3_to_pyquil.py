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

if TYPE_CHECKING:
    from pyquil import Program

    from qbraid.programs.typer import QasmStringType

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


@weight(1.0)  # pylint: disable-next=too-many-statements
def openqasm3_to_pyquil(program: QasmStringType | ast.Program) -> Program:
    """Returns a pyQuil Program equivalent to the input OpenQASM 3 program.

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

    # pass 2: emit gates + measurements
    for statement in unrolled.statements:
        # QuantumPhase = global phase (gphase); unobservable, safe to drop (pyqasm emits
        # it when decomposing gates such as rzz; equivalence holds up to global phase).
        if isinstance(
            statement,
            (ast.QubitDeclaration, ast.ClassicalDeclaration, ast.Include, ast.QuantumPhase),
        ):
            continue

        if isinstance(statement, ast.QuantumGate):
            name = statement.name.name.lower()
            if statement.modifiers:
                raise ProgramConversionError(f"Gate modifiers are not supported: {name}")
            params = [arg.value for arg in statement.arguments]
            qubits = [_flat_qubit(q, qubit_offsets) for q in statement.qubits]

            if name == "sdg":
                quil += pyquil_gates.S(*qubits).dagger()
            elif name == "tdg":
                quil += pyquil_gates.T(*qubits).dagger()
            elif name == "sx":
                quil += pyquil_gates.RX(math.pi / 2, *qubits)
            elif name == "sxdg":
                quil += pyquil_gates.RX(-math.pi / 2, *qubits)
            elif name in ("u", "u3"):
                quil += pyquil_gates.U(*params, *qubits)
            elif name in _GATE_MAP:
                quil += getattr(pyquil_gates, _GATE_MAP[name])(*params, *qubits)
            else:
                raise ProgramConversionError(f"Unsupported gate: {name}")

        elif isinstance(statement, ast.QuantumMeasurementStatement):
            src = _flat_qubit(statement.measure.qubit, qubit_offsets)
            if statement.target is not None and ro is not None:
                target = statement.target
                ro_index = clbit_offsets[target.name.name] + target.indices[0][0].value
                quil += pyquil_gates.MEASURE(src, ro[ro_index])
            else:
                quil += pyquil_gates.MEASURE(src, None)

        else:
            raise ProgramConversionError(f"Unsupported statement: {statement}")

    return quil

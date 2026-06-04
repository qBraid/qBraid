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
Module containing OpenQASM 3 to pyQuil conversion function.
"""
from __future__ import annotations

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


# Gate mapping from OpenQASM3 to pyQuil
GATE_MAP = {
    # Single-qubit gates
    "x": "X",
    "y": "Y",
    "z": "Z",
    "h": "H",
    "s": "S",
    "sdg": "S",
    "t": "T",
    "tdg": "T",
    # Single-qubit rotation gates
    "rx": "RX",
    "ry": "RY",
    "rz": "RZ",
    # Two-qubit gates
    "cx": "CNOT",
    "cnot": "CNOT",
    "cz": "CZ",
    "swap": "SWAP",
    # Three-qubit gates
    "ccx": "CCNOT",
    "ccnot": "CCNOT",
    "toffoli": "CCNOT",
}


def _qubit_index(qubit: ast.IndexedIdentifier | ast.Identifier) -> int:
    """Extract qubit index from OpenQASM3 qubit identifier."""
    if isinstance(qubit, ast.Identifier):
        # Single qubit without index, return 0
        return 0
    
    assert isinstance(qubit, ast.IndexedIdentifier), f"Expected IndexedIdentifier, got {type(qubit)}"
    assert len(qubit.indices) == 1, f"Multi-dimensional qubit arrays not supported: {qubit}"
    assert len(qubit.indices[0]) == 1, f"Expected single index, got {qubit.indices[0]}"
    
    index = qubit.indices[0][0]
    assert isinstance(index, ast.IntegerLiteral), f"Expected IntegerLiteral, got {type(index)}"
    
    return index.value


def _extract_gate_params(statement: ast.QuantumGate) -> list[float]:
    """Extract numeric parameters from a quantum gate statement."""
    params = []
    for arg in statement.arguments:
        if arg.value is not None:
            if isinstance(arg.value, (int, float)):
                params.append(float(arg.value))
            elif isinstance(arg.value, ast.IntegerLiteral):
                params.append(float(arg.value.value))
            elif isinstance(arg.value, ast.FloatLiteral):
                params.append(arg.value.value)
    return params


@weight(0.9)
def openqasm3_to_pyquil(program: QasmStringType | ast.Program) -> Program:
    """Convert an OpenQASM3 program to a pyQuil Program.

    Args:
        program: OpenQASM3 program as a string or ast.Program.

    Returns:
        pyquil.Program: Equivalent pyQuil program.

    Raises:
        ProgramConversionError: If the program cannot be converted.

    Limitations:
        - Only supports gates in GATE_MAP (X, Y, Z, H, S, T, RX, RY, RZ, CNOT, CZ, SWAP, CCNOT)
        - Does not support reset operations
        - Does not support barrier operations
        - Does not support gate modifiers (pow, ctrl, inv)
        - Does not support multi-dimensional qubit arrays
        - Does not support classical control flow (if, for, while)
        - Does not support custom gate definitions
        - Rotation gates only accept single parameter (params[0])
        - Measurements are supported but classical bit handling is simplified
    """
    try:
        module = pyqasm.loads(program)
        module.validate()
    except Exception as e:
        raise ProgramConversionError(f"Invalid OpenQASM3 program: {e}") from e

    module.unroll()
    ast_program = module.unrolled_ast

    quil_program = pyquil.Program()
    qubit_count = 0

    # First pass: count qubits from declarations
    for statement in ast_program.statements:
        if isinstance(statement, ast.QubitDeclaration):
            qubit_count = max(qubit_count, statement.size.value)

    # Declare qubits in pyQuil
    for i in range(qubit_count):
        quil_program.declare(f"ro[{i}]", "BIT", 0)

    # Process gates
    for statement in ast_program.statements:
        if isinstance(statement, ast.Include):
            # Skip include statements (stdgates.inc, qelib1.inc)
            continue
        elif isinstance(statement, ast.QubitDeclaration):
            # Qubit declaration already handled
            continue
        elif isinstance(statement, ast.QuantumGate):
            gate_name = statement.name.name.lower()
            
            # Map gate name to pyQuil
            if gate_name not in GATE_MAP:
                raise ProgramConversionError(f"Unsupported gate: {gate_name}")
            
            pyquil_gate = GATE_MAP[gate_name]
            
            # Extract qubit indices
            qubit_indices = [_qubit_index(q) for q in statement.qubits]
            
            # Extract parameters if any
            params = _extract_gate_params(statement)
            
            # Apply gate in pyQuil using gate builders
            from pyquil.gates import (
                X, Y, Z, H, S, T,
                RX, RY, RZ,
                CNOT, CZ, SWAP,
                CCNOT,
            )
            
            gate_map = {
                "X": X, "Y": Y, "Z": Z, "H": H, "S": S, "T": T,
                "RX": RX, "RY": RY, "RZ": RZ,
                "CNOT": CNOT, "CZ": CZ, "SWAP": SWAP,
                "CCNOT": CCNOT,
            }
            
            gate_class = gate_map.get(pyquil_gate)
            if gate_class is None:
                raise ProgramConversionError(f"Gate mapping not found: {pyquil_gate}")
            
            # Create gate instance with qubit indices and parameters
            if len(params) == 0:
                gate = gate_class(*qubit_indices)
            else:
                gate = gate_class(params[0], *qubit_indices)
            
            # Apply gate to program
            quil_program += gate
        elif isinstance(statement, ast.QuantumMeasurement):
            # Handle measurement
            qubit_idx = _qubit_index(statement.measure.qubit)
            if statement.target is not None:
                classical_idx = _qubit_index(statement.target)
                quil_program.measure(qubit_idx, classical_idx)
        else:
            # Skip other statement types (classical declarations, etc.)
            continue

    return quil_program

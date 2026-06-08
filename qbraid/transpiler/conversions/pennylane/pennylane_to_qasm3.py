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
Module defining PennyLane to OpenQASM 3.0 conversion

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pennylane.tape import QuantumScript

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    from qbraid.programs.typer import Qasm3StringType

_PENNYLANE_TO_QASM3_GATE_MAP: dict[str, str] = {
    "Hadamard": "h",
    "PauliX": "x",
    "PauliY": "y",
    "PauliZ": "z",
    "S": "s",
    "T": "t",
    "SX": "sx",
    "Adjoint(S)": "sdg",
    "Adjoint(T)": "tdg",
    "Adjoint(SX)": "sxdg",
    "RX": "rx",
    "RY": "ry",
    "RZ": "rz",
    "PhaseShift": "p",
    "CNOT": "cx",
    "CZ": "cz",
    "SWAP": "swap",
    "Toffoli": "ccx",
    "CSWAP": "cswap",
    "CPhaseShift": "cp",
    "IsingXX": "rxx",
    "IsingYY": "ryy",
    "IsingZZ": "rzz",
    "U1": "u1",
    "U2": "u2",
    "U3": "u3",
    "CRX": "crx",
    "CRY": "cry",
    "CRZ": "crz",
    "Identity": "id",
}


@weight(1)
def pennylane_to_qasm3(tape: QuantumScript) -> "Qasm3StringType":
    """Converts a PennyLane QuantumScript (tape) to an OpenQASM 3.0 string.

    Gate mapping covers the full ``stdgates.inc`` standard library, including
    single-qubit Clifford gates (H, X, Y, Z, S, T, SX and their adjoints),
    rotation gates (RX, RY, RZ, PhaseShift), two-qubit entangling gates
    (CNOT/CX, CZ, SWAP, CPhaseShift, CRX/CRY/CRZ, IsingXX/YY/ZZ), and
    three-qubit gates (Toffoli/CCX, CSWAP).

    Args:
        tape (QuantumScript): input PennyLane tape or QuantumScript.

    Returns:
        str: OpenQASM 3.0 representation of the tape.

    Raises:
        ValueError: If an unsupported PennyLane gate is encountered.
    """
    all_wires = tape.wires.tolist()
    n_qubits = len(all_wires)
    wire_index = {w: i for i, w in enumerate(all_wires)}

    lines = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        f"qubit[{n_qubits}] q;",
    ]

    for op in tape.operations:
        name = op.name
        if name not in _PENNYLANE_TO_QASM3_GATE_MAP:
            raise ValueError(
                f"Unsupported PennyLane gate '{name}' for QASM3 conversion. "
                f"Supported gates: {sorted(_PENNYLANE_TO_QASM3_GATE_MAP.keys())}"
            )
        qasm_name = _PENNYLANE_TO_QASM3_GATE_MAP[name]
        wires = [wire_index[w] for w in op.wires.tolist()]
        qubit_str = ", ".join(f"q[{w}]" for w in wires)

        if op.parameters:
            param_str = ", ".join(str(float(p)) for p in op.parameters)
            lines.append(f"{qasm_name}({param_str}) {qubit_str};")
        else:
            lines.append(f"{qasm_name} {qubit_str};")

    return "\n".join(lines) + "\n"

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
    "ControlledPhaseShift": "cp",
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
    "Measure": "measure",
    "MidMeasureMP": "measure",
    "Reset": "reset",
    "Conditional": "conditional",
}


@weight(1)
def pennylane_to_qasm3(tape: QuantumScript) -> "Qasm3StringType":
    """Converts a PennyLane QuantumScript (tape) to an OpenQASM 3.0 string.

    Gate mapping covers the full ``stdgates.inc`` standard library, including
    single-qubit Clifford gates (H, X, Y, Z, S, T, SX and their adjoints),
    rotation gates (RX, RY, RZ, PhaseShift), two-qubit entangling gates
    (CNOT/CX, CZ, SWAP, CPhaseShift, CRX/CRY/CRZ, IsingXX/YY/ZZ), and
    three-qubit gates (Toffoli/CCX, CSWAP).

    Additionally supports dynamic circuits with conditional operations (qml.cond),
    generating QASM3 native if/else syntax: ``if (c[i] == 1) { gate q[j]; }``.
    This provides a significant advantage over the pennylane → QASM2 → QASM3 path,
    as QASM2 cannot represent complex conditional logic and would lose or degrade
    these operations during the intermediate conversion.

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

    # classical registers for measurements
    meas_ops = [op for op in tape.operations if op.name == "Measure"] + [
        obs for obs in getattr(tape, "observables", []) if getattr(obs, "name", "") == "Measure"
    ]
    measurements = getattr(tape, "measurements", [])
    if meas_ops or measurements:
        lines.append(f"bit[{n_qubits}] c;")

    for op in tape.operations:
        name = op.name
        # Check if name starts with "Conditional" (e.g., "Conditional(PauliX)")
        is_conditional = name.startswith("Conditional")
        
        if not is_conditional and name not in _PENNYLANE_TO_QASM3_GATE_MAP:
            raise ValueError(
                f"Unsupported PennyLane gate '{name}' for QASM3 conversion. "
                f"Supported gates: {sorted(_PENNYLANE_TO_QASM3_GATE_MAP.keys())}"
            )
        
        qasm_name = _PENNYLANE_TO_QASM3_GATE_MAP.get(name, name) if not is_conditional else "conditional"
        wires = [wire_index[w] for w in op.wires.tolist()]
        qubit_str = ", ".join(f"q[{w}]" for w in wires)

        if name == "Measure" or name == "MidMeasureMP":
            # measure q[i] -> c[i];
            for w in wires:
                lines.append(f"measure q[{w}] -> c[{w}];")
        elif name == "Reset":
            for w in wires:
                lines.append(f"reset q[{w}];")
        elif is_conditional:
            # Handle conditional operations (qml.cond)
            # QASM3 syntax: if (c[i] == 1) { gate q[j]; }
            if hasattr(op, "meas_val") and hasattr(op, "base"):
                meas_val = op.meas_val
                then_op = op.base  # PennyLane uses 'base' for the conditional operation
                
                # Get classical bit index from measurement
                if hasattr(meas_val, "wires") and meas_val.wires:
                    meas_wire = meas_val.wires.tolist()[0]
                    c_idx = wire_index.get(meas_wire, 0)
                else:
                    c_idx = 0
                
                # Get condition value (default to 1 for typical qml.cond usage)
                condition_val = 1
                if hasattr(op, "condition_value"):
                    condition_val = op.condition_value
                elif hasattr(meas_val, "branches"):
                    # Get the first branch value
                    branch_keys = list(meas_val.branches.keys())
                    if branch_keys:
                        condition_val = branch_keys[0][0] if branch_keys[0] else 1
                
                # Get the conditional gate
                cond_gate_name = then_op.name
                if cond_gate_name in _PENNYLANE_TO_QASM3_GATE_MAP:
                    cond_qasm_name = _PENNYLANE_TO_QASM3_GATE_MAP[cond_gate_name]
                    cond_wires = [wire_index[w] for w in then_op.wires.tolist()]
                    cond_qubit_str = ", ".join(f"q[{w}]" for w in cond_wires)
                    
                    # Generate QASM3 conditional syntax
                    if then_op.parameters:
                        param_str = ", ".join(str(float(p)) for p in then_op.parameters)
                        lines.append(f"if (c[{c_idx}] == {condition_val}) {{ {cond_qasm_name}({param_str}) {cond_qubit_str}; }}")
                    else:
                        lines.append(f"if (c[{c_idx}] == {condition_val}) {{ {cond_qasm_name} {cond_qubit_str}; }}")
                else:
                    raise ValueError(
                        f"Unsupported conditional gate '{cond_gate_name}' for QASM3 conversion. "
                        f"Supported gates: {sorted(_PENNYLANE_TO_QASM3_GATE_MAP.keys())}"
                    )
        elif op.parameters:
            param_str = ", ".join(str(float(p)) for p in op.parameters)
            lines.append(f"{qasm_name}({param_str}) {qubit_str};")
        else:
            lines.append(f"{qasm_name} {qubit_str};")

    # Process mid-circuit measurements from tape.measurements (PennyLane 0.42+)
    for meas in measurements:
        if hasattr(meas, "wires"):
            for w in meas.wires.tolist():
                w_idx = wire_index.get(w)
                if w_idx is not None:
                    lines.append(f"measure q[{w_idx}] -> c[{w_idx}];")

    return "\n".join(lines) + "\n"

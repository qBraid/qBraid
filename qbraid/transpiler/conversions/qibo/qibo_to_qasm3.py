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

"""Function for converting a Qibo circuit to an OpenQASM 3 string."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.exceptions import ProgramConversionError

if TYPE_CHECKING:
    import qibo.models

# Qibo gate class name → QASM 3 gate name (single-qubit, no parameters)
_ONE_QUBIT: dict[str, str] = {
    "H": "h",
    "X": "x",
    "Y": "y",
    "Z": "z",
    "S": "s",
    "SDG": "sdg",
    "T": "t",
    "TDG": "tdg",
    "SX": "sx",
    "SXDG": "sxdg",
    "I": "id",
}

# Qibo gate class name → QASM 3 gate name (single-qubit, parametric)
_ONE_QUBIT_PARAM: dict[str, str] = {
    "RX": "rx",
    "RY": "ry",
    "RZ": "rz",
    "U1": "p",
    "U3": "u",
}

# Qibo gate class name → QASM 3 gate name (two-qubit)
_TWO_QUBIT: dict[str, str] = {
    "CNOT": "cx",
    "CX": "cx",
    "CZ": "cz",
    "SWAP": "swap",
    "ISWAP": "iswap",
    "ECR": "ecr",
    "CRX": "crx",
    "CRY": "cry",
    "CRZ": "crz",
    "CP": "cp",
    "CU1": "cp",
}

# Qibo gate class name → QASM 3 gate name (three-qubit)
_THREE_QUBIT: dict[str, str] = {
    "TOFFOLI": "ccx",
    "CSWAP": "cswap",
}


def qibo_to_qasm3(circuit: "qibo.models.Circuit") -> str:
    """Convert a :class:`qibo.models.Circuit` to an OpenQASM 3 string.

    Only circuits composed of gates from ``stdgates.inc`` are supported.
    Custom gate definitions are not handled.

    Args:
        circuit: Qibo circuit to convert.

    Returns:
        OpenQASM 3 source string equivalent to ``circuit``.

    Raises:
        ProgramConversionError: If the circuit contains an unsupported gate
            that cannot be expressed in ``stdgates.inc``.

    Example:
        >>> import qibo
        >>> from qibo import gates
        >>> c = qibo.models.Circuit(2)
        >>> c.add(gates.H(0))
        >>> c.add(gates.CNOT(0, 1))
        >>> c.add(gates.M(0, 1))
        >>> print(qibo_to_qasm3(c))
        OPENQASM 3.0;
        include "stdgates.inc";
        qubit[2] q;
        bit[2] c;
        h q[0];
        cx q[0], q[1];
        measure q[0] -> c[0];
        measure q[1] -> c[1];
    """
    nqubits = circuit.nqubits
    lines = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        f"qubit[{nqubits}] q;",
    ]

    measure_gates = [g for g in circuit.queue if type(g).__name__ == "M"]
    num_cbits = sum(len(g.target_qubits) for g in measure_gates)
    if num_cbits > 0:
        lines.append(f"bit[{num_cbits}] c;")

    cbit_index = 0

    for gate in circuit.queue:
        name = type(gate).__name__.upper()

        if name == "M":
            for qubit in gate.target_qubits:
                lines.append(f"measure q[{qubit}] -> c[{cbit_index}];")
                cbit_index += 1

        elif name in _ONE_QUBIT:
            lines.append(f"{_ONE_QUBIT[name]} q[{gate.target_qubits[0]}];")

        elif name in _ONE_QUBIT_PARAM:
            qasm_name = _ONE_QUBIT_PARAM[name]
            params = ", ".join(f"{p:.10g}" for p in gate.parameters)
            lines.append(f"{qasm_name}({params}) q[{gate.target_qubits[0]}];")

        elif name in _TWO_QUBIT:
            qasm_name = _TWO_QUBIT[name]
            qubits = list(gate.control_qubits) + list(gate.target_qubits)
            qubit_str = ", ".join(f"q[{q}]" for q in qubits)
            if gate.parameters:
                params = ", ".join(f"{p:.10g}" for p in gate.parameters)
                lines.append(f"{qasm_name}({params}) {qubit_str};")
            else:
                lines.append(f"{qasm_name} {qubit_str};")

        elif name in _THREE_QUBIT:
            qubits = list(gate.control_qubits) + list(gate.target_qubits)
            qubit_str = ", ".join(f"q[{q}]" for q in qubits)
            lines.append(f"{_THREE_QUBIT[name]} {qubit_str};")

        else:
            raise ProgramConversionError(
                f"Gate '{name}' is not supported by qibo_to_qasm3. "
                "Decompose it into stdgates.inc gates before converting."
            )

    return "\n".join(lines)

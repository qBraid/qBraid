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
Module defining pyQuil to OpenQASM 3 conversion function.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError

quilbase = LazyLoader("quilbase", globals(), "pyquil.quilbase")

if TYPE_CHECKING:
    import pyquil

    from qbraid.programs.typer import Qasm3StringType

# pyQuil gate name -> OpenQASM 3 (stdgates.inc) gate name. The inverse of the
# mapping used by ``openqasm3_to_pyquil``, restricted to gates that are defined
# in ``stdgates.inc`` so the emitted program is self-contained.
_GATE_MAP = {
    # one-qubit, no parameters
    "I": "id",
    "X": "x",
    "Y": "y",
    "Z": "z",
    "H": "h",
    "S": "s",
    "T": "t",
    # one-qubit, parameterized
    "RX": "rx",
    "RY": "ry",
    "RZ": "rz",
    "PHASE": "p",
    "U": "u",
    # two-qubit, no parameters
    "CNOT": "cx",
    "CZ": "cz",
    "SWAP": "swap",
    # two-qubit, parameterized
    "CPHASE": "cp",
    # three-qubit
    "CCNOT": "ccx",
    "CSWAP": "cswap",
}

# pyQuil gate (under a single DAGGER modifier) -> OpenQASM 3 adjoint gate.
_DAGGER_MAP = {"S": "sdg", "T": "tdg"}


def _angle(param: object) -> float:
    """Return the real angle of a numeric pyQuil gate parameter."""
    try:
        value = complex(param)  # type: ignore[arg-type]
    except (TypeError, ValueError) as err:
        raise ProgramConversionError(f"Unsupported non-numeric gate parameter: {param!r}") from err
    if value.imag != 0.0:
        raise ProgramConversionError(f"Unsupported complex gate parameter: {param!r}")
    return value.real


@weight(1)
def pyquil_to_qasm3(program: pyquil.quil.Program) -> Qasm3StringType:
    """Returns an OpenQASM 3 string equivalent to the input pyQuil Program.

    Args:
        program (pyquil.quil.Program): pyQuil Program to convert.

    Returns:
        str: OpenQASM 3 string equivalent to the input program.

    Raises:
        ProgramConversionError: If the program contains an instruction, gate, or
            modifier that this conversion does not support.
    """
    qubits = program.get_qubits()
    num_qubits = (max(qubits) + 1) if qubits else 0

    lines = ["OPENQASM 3.0;", 'include "stdgates.inc";']
    if num_qubits:
        lines.append(f"qubit[{num_qubits}] q;")

    # classical BIT registers declared via DECLARE become bit registers
    bit_registers: set[str] = set()
    for instruction in program.instructions:
        if isinstance(instruction, quilbase.Declare) and instruction.memory_type == "BIT":
            lines.append(f"bit[{instruction.memory_size}] {instruction.name};")
            bit_registers.add(instruction.name)

    for instruction in program.instructions:
        if isinstance(instruction, quilbase.Declare):
            continue

        if isinstance(instruction, quilbase.Gate):
            if instruction.modifiers:
                if instruction.modifiers == ["DAGGER"] and instruction.name in _DAGGER_MAP:
                    name = _DAGGER_MAP[instruction.name]
                else:
                    raise ProgramConversionError(
                        f"Unsupported modifier(s) {instruction.modifiers} on {instruction.name}"
                    )
            elif instruction.name in _GATE_MAP:
                name = _GATE_MAP[instruction.name]
            else:
                raise ProgramConversionError(f"Unsupported gate: {instruction.name}")

            targets = ", ".join(f"q[{qubit.index}]" for qubit in instruction.qubits)
            if instruction.params:
                params = ", ".join(str(_angle(param)) for param in instruction.params)
                lines.append(f"{name}({params}) {targets};")
            else:
                lines.append(f"{name} {targets};")

        elif isinstance(instruction, quilbase.Measurement):
            src = instruction.qubit.index
            target = instruction.classical_reg
            if target is not None and target.name in bit_registers:
                lines.append(f"{target.name}[{target.offset}] = measure q[{src}];")
            else:
                lines.append(f"measure q[{src}];")

        else:
            raise ProgramConversionError(f"Unsupported instruction: {instruction}")

    return "\n".join(lines) + "\n"

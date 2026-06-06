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

# pyQuil gate name -> OpenQASM 3 gate name. The inverse of the mapping used by
# ``openqasm3_to_pyquil``, restricted to gates recognized by qBraid's ``pyqasm``
# engine (the official ``stdgates.inc`` set plus pyqasm built-ins such as
# ``iswap``/``rxx``/``xy``/``cphaseshift*``) so the emitted program round-trips.
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
    "ISWAP": "iswap",
    # two-qubit, parameterized
    "CPHASE": "cp",
    "CPHASE00": "cphaseshift00",
    "CPHASE01": "cphaseshift01",
    "CPHASE10": "cphaseshift10",
    "PSWAP": "pswap",
    "XY": "xy",
    "RXX": "rxx",
    "RYY": "ryy",
    "RZZ": "rzz",
    # three-qubit
    "CCNOT": "ccx",
    "CSWAP": "cswap",
}

# pyQuil gate (under a single DAGGER modifier) -> OpenQASM 3 adjoint gate.
_DAGGER_MAP = {"S": "sdg", "T": "tdg"}


def _qubit_index(qubit: object) -> int:
    """Return the integer index of a concrete pyQuil qubit.

    ``QubitPlaceholder``/``FormalArgument`` (e.g. from parsed Quil text or
    DefCircuit bodies) expose an ``.index`` property that *raises* when no fixed
    index is assigned, so that is converted into a clear ``ProgramConversionError``.
    """
    if isinstance(qubit, int):
        return qubit
    try:
        index = qubit.index  # type: ignore[attr-defined]
    except (AttributeError, ValueError, RuntimeError) as err:
        raise ProgramConversionError(f"Unsupported non-fixed qubit reference: {qubit!r}") from err
    if not isinstance(index, int):
        raise ProgramConversionError(f"Unsupported non-fixed qubit reference: {qubit!r}")
    return index


def _angle(param: object) -> float:
    """Return the real angle of a numeric pyQuil gate parameter."""
    try:
        value = complex(param)  # type: ignore[arg-type]
    except (TypeError, ValueError) as err:
        raise ProgramConversionError(f"Unsupported non-numeric gate parameter: {param!r}") from err
    if value.imag != 0.0:
        raise ProgramConversionError(f"Unsupported complex gate parameter: {param!r}")
    return value.real


@weight(1)  # pylint: disable-next=too-many-statements
def pyquil_to_qasm3(program: pyquil.quil.Program) -> Qasm3StringType:
    """Returns an OpenQASM 3 string equivalent to the input pyQuil Program.

    Supports the gates recognized by ``pyqasm`` (Clifford+T, rotations, ``U``,
    ``iswap``/``pswap``/``xy``/``rxx``/``ryy``/``rzz``/``cphaseshift00|01|10``),
    ``S``/``T`` daggers, measurement, ``RESET`` (-> ``reset``), ``FENCE``
    (-> ``barrier``), and ``DELAY`` (-> ``delay``).

    Known limitation: classical feed-forward (pyQuil ``JUMP``/``JUMP-WHEN``) has
    no straightforward OpenQASM 3 structured-control reconstruction and raises
    ``ProgramConversionError`` rather than being silently dropped.

    Args:
        program (pyquil.quil.Program): pyQuil Program to convert.

    Returns:
        str: OpenQASM 3 string equivalent to the input program.

    Raises:
        ProgramConversionError: If the program contains an instruction, gate, or
            modifier that this conversion does not support.
    """
    qubits = {_qubit_index(q) for q in program.get_qubit_indices()}
    num_qubits = (max(qubits) + 1) if qubits else 0

    lines = ["OPENQASM 3.0;", 'include "stdgates.inc";']
    if num_qubits:
        lines.append(f"qubit[{num_qubits}] q;")

    # classical BIT registers declared via DECLARE become bit registers
    bit_registers: dict[str, int] = {}
    for instruction in program.instructions:
        if isinstance(instruction, quilbase.Declare) and instruction.memory_type == "BIT":
            lines.append(f"bit[{instruction.memory_size}] {instruction.name};")
            bit_registers[instruction.name] = instruction.memory_size

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

            targets = ", ".join(f"q[{_qubit_index(qubit)}]" for qubit in instruction.qubits)
            if instruction.params:
                params = ", ".join(str(_angle(param)) for param in instruction.params)
                lines.append(f"{name}({params}) {targets};")
            else:
                lines.append(f"{name} {targets};")

        elif isinstance(instruction, quilbase.Measurement):
            src = _qubit_index(instruction.qubit)
            target = instruction.classical_reg
            if target is None:
                lines.append(f"measure q[{src}];")
            elif target.name in bit_registers and 0 <= target.offset < bit_registers[target.name]:
                lines.append(f"{target.name}[{target.offset}] = measure q[{src}];")
            else:
                raise ProgramConversionError(
                    f"Unsupported measurement target: {target.name}[{target.offset}]"
                )

        elif isinstance(instruction, quilbase.ResetQubit):
            lines.append(f"reset q[{_qubit_index(instruction.qubit)}];")

        elif isinstance(instruction, quilbase.Reset):
            # bare RESET resets the whole register
            for index in range(num_qubits):
                lines.append(f"reset q[{index}];")

        elif isinstance(instruction, quilbase.FenceAll):
            if num_qubits:
                lines.append("barrier " + ", ".join(f"q[{i}]" for i in range(num_qubits)) + ";")

        elif isinstance(instruction, quilbase.Fence):
            targets = ", ".join(f"q[{_qubit_index(q)}]" for q in instruction.qubits)
            lines.append(f"barrier {targets};")

        elif isinstance(instruction, quilbase.DelayQubits):
            targets = ", ".join(f"q[{_qubit_index(q)}]" for q in instruction.qubits)
            lines.append(f"delay[{instruction.duration}s] {targets};")

        else:
            raise ProgramConversionError(f"Unsupported instruction: {instruction}")

    return "\n".join(lines) + "\n"

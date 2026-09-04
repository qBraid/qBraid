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
Module for conversions between Cirq Circuits and QASM strings

"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

import cirq
import pyqasm
from cirq import ops, value

from qbraid._version import __version__ as qbraid_version
from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    from qbraid.programs.typer import Qasm2StringType


_CREG = re.compile(r"^creg\s+(?P<name>\w+)\s*\[(?P<size>\d+)\]\s*;\s*$")
_BIT_INDEX = re.compile(r"^(?P<register>.+)_(?P<index>\d+)$")


def _order_cregs_by_key(qasm: str) -> str:
    """Emit ``creg`` declarations in measurement-key order rather than moment order.

    Cirq writes one ``creg`` per measurement key in the order the measurements are
    scheduled, so an idle qubit whose measurement packs into an earlier moment gets its
    register declared first. Nothing is wrong with the QASM -- each register is named and
    its ``measure`` is correct -- but consumers that flatten the registers into one
    readout region do so in declaration order (``openqasm3_to_pyquil``, matching how
    ``RigettiJob`` reads them back, #1314). Declaration order therefore has to reflect the
    keys, or the flattened bits come out permuted relative to the source.

    Registers are sorted the way ``cirq_to_pyquil`` orders its merged measurements: by the
    ``(register, index)`` parsed from the key, so ``m_c_0`` precedes ``m_c_2``. Names that
    do not carry an index keep their relative order, and the declarations are rewritten in
    place so surrounding statements are untouched.
    """
    lines = qasm.splitlines(keepends=True)
    positions = [i for i, line in enumerate(lines) if _CREG.match(line)]
    if len(positions) < 2:
        return qasm

    def sort_key(index: int) -> tuple:
        name = _CREG.match(lines[index])["name"]
        match = _BIT_INDEX.match(name)
        if match is None:
            return (1, "", 0, index)
        return (0, match["register"], int(match["index"]), index)

    reordered = [lines[i] for i in sorted(positions, key=sort_key)]
    for slot, line in zip(positions, reordered, strict=True):
        lines[slot] = line
    return "".join(lines)


@value.value_equality
class ZPowGate(cirq.ZPowGate):
    """A single qubit gate for rotations around the
    Z axis of the Bloch sphere.
    """

    def _qasm_(self, args: cirq.QasmArgs, qubits: tuple[cirq.Qid, ...]) -> Optional[str]:
        args.validate_version("2.0")
        if self._global_shift == 0:
            if self._exponent == 0.25:
                return args.format("t {0};\n", qubits[0])
            if self._exponent == -0.25:
                return args.format("tdg {0};\n", qubits[0])
            if self._exponent == 0.5:
                return args.format("s {0};\n", qubits[0])
            if self._exponent == -0.5:
                return args.format("sdg {0};\n", qubits[0])
            if self._exponent == 1:
                return args.format("z {0};\n", qubits[0])
            return args.format("p({0:half_turns}) {1};\n", self._exponent, qubits[0])
        return args.format("rz({0:half_turns}) {1};\n", self._exponent, qubits[0])


def map_zpow_and_unroll(circuit: cirq.Circuit) -> cirq.Circuit:
    """Map ZPowGate to RZ and unroll circuit"""

    def _map_zpow(op: cirq.Operation, _: int) -> cirq.OP_TREE:
        if isinstance(op.gate, cirq.ZPowGate):
            yield ZPowGate(exponent=op.gate.exponent, global_shift=op.gate.global_shift)(
                op.qubits[0]
            )
        else:
            yield op

    return cirq.map_operations_and_unroll(circuit, _map_zpow)


def _to_qasm_output(
    circuit: cirq.Circuit,
    header: Optional[str] = None,
    precision: int = 10,
    qubit_order: cirq.QubitOrderOrList = ops.QubitOrder.DEFAULT,
) -> cirq.QasmOutput:
    """Returns a QASM object equivalent to the circuit.

    Args:
        header: A multi-line string that is placed in a comment at the top
            of the QASM. Defaults to a cirq version specifier.
        precision: Number of digits to use when representing numbers.
        qubit_order: Determines how qubits are ordered in the QASM
            register.
    """
    if header is None:
        header = f"Generated from qBraid v{qbraid_version}"
    qubits = ops.QubitOrder.as_qubit_order(qubit_order).order_for(circuit.all_qubits())
    return cirq.QasmOutput(
        operations=circuit.all_operations(),
        qubits=qubits,
        header=header,
        precision=precision,
        version="2.0",
    )


@weight(1)
def cirq_to_qasm2(
    circuit: cirq.Circuit,
    header: Optional[str] = None,
    precision: int = 10,
    qubit_order: cirq.QubitOrderOrList = ops.QubitOrder.DEFAULT,
) -> Qasm2StringType:
    """Returns a QASM string representing the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a QASM string.

    Returns:
        Qasm2StringType: QASM string equivalent to the input Cirq circuit.
    """
    circuit = map_zpow_and_unroll(circuit)
    qasm = _order_cregs_by_key(str(_to_qasm_output(circuit, header, precision, qubit_order)))
    # format the qasm before returning
    return pyqasm.dumps(pyqasm.loads(qasm))

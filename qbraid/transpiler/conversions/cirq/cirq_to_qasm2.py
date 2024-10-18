# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for conversions between Cirq Circuits and QASM strings

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import cirq
from cirq import ops, value

from qbraid._version import __version__ as qbraid_version
from qbraid.passes.qasm.format import format_qasm
from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    from qbraid.programs.typer import Qasm2StringType


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
    qasm = str(_to_qasm_output(circuit, header, precision, qubit_order))
    return format_qasm(qasm)

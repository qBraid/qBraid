# Copyright (C) 2023 qBraid
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
from typing import Optional

import cirq
from cirq import ops

import qbraid
from qbraid.interface.qbraid_qasm.qasm_preprocess import convert_to_supported_qasm
from qbraid.transpiler.cirq_qasm.qasm_parser import QasmParser

QASMType = str


def _to_qasm_output(
    circuit: cirq.Circuit,
    header: Optional[str] = None,
    precision: int = 10,
    qubit_order: "cirq.QubitOrderOrList" = ops.QubitOrder.DEFAULT,
) -> "cirq.QasmOutput":
    """Returns a QASM object equivalent to the circuit.

    Args:
        header: A multi-line string that is placed in a comment at the top
            of the QASM. Defaults to a cirq version specifier.
        precision: Number of digits to use when representing numbers.
        qubit_order: Determines how qubits are ordered in the QASM
            register.
    """
    if header is None:
        header = f"Generated from qBraid v{qbraid._version.__version__}"
    qubits = ops.QubitOrder.as_qubit_order(qubit_order).order_for(circuit.all_qubits())
    return cirq.QasmOutput(
        operations=circuit.all_operations(),
        qubits=qubits,
        header=header,
        precision=precision,
        version="2.0",
    )


def to_qasm(
    circuit: cirq.Circuit,
    header: Optional[str] = None,
    precision: int = 10,
    qubit_order: "cirq.QubitOrderOrList" = ops.QubitOrder.DEFAULT,
) -> QASMType:
    """Returns a QASM string representing the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a QASM string.

    Returns:
        QASMType: QASM string equivalent to the input Cirq circuit.
    """
    return str(_to_qasm_output(circuit, header, precision, qubit_order))


def from_qasm(qasm: QASMType) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input QASM string.

    Args:
        qasm: QASM string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input QASM string.
    """
    qasm = convert_to_supported_qasm(qasm)
    return QasmParser().parse(qasm).circuit

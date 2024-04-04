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
from cirq.contrib.qasm_import.exception import QasmException as CirqQasmException

from qbraid._version import __version__ as qbraid_version
from qbraid.programs.exceptions import QasmError as QbraidQasmError
from qbraid.programs.qasm_passes import flatten_qasm_program

from .cirq_gates import _map_zpow_and_unroll
from .cirq_qasm_parser import QasmParser

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
        header = f"Generated from qBraid v{qbraid_version}"
    qubits = ops.QubitOrder.as_qubit_order(qubit_order).order_for(circuit.all_qubits())
    return cirq.QasmOutput(
        operations=circuit.all_operations(),
        qubits=qubits,
        header=header,
        precision=precision,
        version="2.0",
    )


def cirq_to_qasm2(
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
    circuit = _map_zpow_and_unroll(circuit)
    return str(_to_qasm_output(circuit, header, precision, qubit_order))


def qasm2_to_cirq(qasm: QASMType) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input QASM string.

    Args:
        qasm: QASM string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input QASM string.
    """
    try:
        qasm = flatten_qasm_program(qasm)
        return QasmParser().parse(qasm).circuit
    except CirqQasmException as err:
        raise QbraidQasmError from err

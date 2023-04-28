# Copyright 2023 qBraid
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
from typing import Optional

import cirq
from cirq import ops

import qbraid
from qbraid.transpiler.cirq_qasm.qasm_parser import QasmParser
from qbraid.transpiler.cirq_qasm.qasm_preprocess import convert_to_supported_qasm

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

# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re
from typing import Optional

import cirq
from cirq import circuits, ops

from qbraid.transpiler.cirq_utils.qasm_output import QasmOutput
from qbraid.transpiler.cirq_utils.qasm_parser import QasmParser

QASMType = str


def _remove_qasm_barriers(qasm: QASMType) -> QASMType:
    """Returns a copy of the input QASM with all barriers removed.

    Args:
        qasm: QASM to remove barriers from.

    Note:
        According to the OpenQASM 2.X language specification
        (https://arxiv.org/pdf/1707.03429v2.pdf), "Statements are separated by
        semicolons. Whitespace is ignored. The language is case sensitive.
        Comments begin with a pair of forward slashes and end with a new line."
    """
    quoted_re = r"(?:\"[^\"]*?\")"
    statement_re = r"((?:[^;{}\"]*?" + quoted_re + r"?)*[;{}])?"
    comment_re = r"(\n?//[^\n]*(?:\n|$))?"
    statements_comments = re.findall(statement_re + comment_re, qasm)
    lines = []
    for statement, comment in statements_comments:
        if re.match(r"^\s*barrier(?:(?:\s+)|(?:;))", statement) is None:
            lines.append(statement + comment)
    return "".join(lines)


def _to_qasm_output(
    circuit: circuits.Circuit,
    header: Optional[str] = None,
    precision: int = 10,
    qubit_order: "cirq.QubitOrderOrList" = ops.QubitOrder.DEFAULT,
) -> QasmOutput:
    """Returns a QASM object equivalent to the circuit.
    Args:
        header: A multi-line string that is placed in a comment at the top
            of the QASM. Defaults to a cirq version specifier.
        precision: Number of digits to use when representing numbers.
        qubit_order: Determines how qubits are ordered in the QASM
            register.
    """
    if header is None:
        header = f"Generated from Cirq v{cirq._version.__version__}"
    qubits = ops.QubitOrder.as_qubit_order(qubit_order).order_for(circuit.all_qubits())
    return QasmOutput(
        operations=circuit.all_operations(),
        qubits=qubits,
        header=header,
        precision=precision,
        version="2.0",
    )


def circuit_to_qasm(
    circuit: circuits.Circuit,
    header: Optional[str] = None,
    precision: int = 10,
    qubit_order: "cirq.QubitOrderOrList" = ops.QubitOrder.DEFAULT,
) -> QASMType:
    """Converts a `cirq.Circuit` to an OpenQASM string.
    Args:
        circuit: cirq Circuit object
        header: A multi-line string that is placed in a comment at the top
            of the QASM. Defaults to a cirq version specifier.
        precision: Number of digits to use when representing numbers.
        qubit_order: Determines how qubits are ordered in the QASM
            register.
    """

    return str(_to_qasm_output(circuit, header, precision, qubit_order))


def circuit_from_qasm(qasm: str) -> circuits.Circuit:
    """Parses an OpenQASM string to `cirq.Circuit`.
    Args:
        qasm: The OpenQASM string
    Returns:
        The parsed circuit
    """

    return QasmParser().parse(qasm).circuit


def to_qasm(circuit: cirq.Circuit) -> QASMType:
    """Returns a QASM string representing the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a QASM string.

    Returns:
        QASMType: QASM string equivalent to the input Cirq circuit.
    """
    # Simplify exponents of gates. For example, H**-1 is simplified to H.
    # _simplify_circuit_exponents(circuit)
    return circuit.to_qasm()


def from_qasm(qasm: QASMType) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input QASM string.

    Args:
        qasm: QASM string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input QASM string.
    """
    qasm = _remove_qasm_barriers(qasm)
    return circuit_from_qasm(qasm)

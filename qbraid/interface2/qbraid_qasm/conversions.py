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
from typing import Optional

import cirq
from cirq import circuits, ops

from qbraid.interface2.qbraid_qasm.parser import QasmParser
from qbraid.interface2.qbraid_qasm.output import QasmOutput

QASMType = str


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


def cirq_to_qasm(
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


def cirq_from_qasm(qasm: str) -> circuits.Circuit:
    """Parses an OpenQASM string to `cirq.Circuit`.
    Args:
        qasm: The OpenQASM string
    Returns:
        The parsed circuit
    """

    return QasmParser().parse(qasm).circuit

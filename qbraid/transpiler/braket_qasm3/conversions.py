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
Module for converting Braket circuits to/from OpenQASM 3

"""

from braket.circuits import Circuit
from braket.circuits.serialization import IRType
from braket.ir.openqasm import Program as OpenQasmProgram

from qbraid.exceptions import QasmError

QASMType = str


def braket_to_qasm3(circuit: Circuit) -> QASMType:
    """Converts a ``braket.circuits.Circuit`` to an OpenQASM 3.0 string.

    .. code-block:: python

        >>> from braket.circuits import Circuit
        >>> circuit = Circuit().h(0).cnot(0,1).cnot(1,2)
        >>> print(circuit)
        T  : |0|1|2|

        q0 : -H-C---
                |
        q1 : ---X-C-
                  |
        q2 : -----X-

        T  : |0|1|2|
        >>> print(braket_to_qasm3(circuit))
        OPENQASM 3.0;
        bit[3] b;
        qubit[3] q;
        h q[0];
        cnot q[0], q[1];
        cnot q[1], q[2];
        b[0] = measure q[0];
        b[1] = measure q[1];
        b[2] = measure q[2];

    Args:
        circuit: Amazon Braket quantum circuit

    Returns:
        The OpenQASM 3.0 string equivalent to the circuit

    Raises:
        CircuitConversionError: If braket to qasm conversion fails

    """
    try:
        return circuit.to_ir(IRType.OPENQASM).source
    except Exception as err:
        raise QasmError("Error converting braket circuit to qasm3 string") from err


def braket_from_qasm3(qasm_str: QASMType) -> Circuit:
    """Converts an OpenQASM 3.0 string to a ``braket.circuits.Circuit``.

    Args:
        circuit: OpenQASM 3 string

    Returns:
        The Amazon Braket circuit equivalent to the input OpenQASM 3.0 string

    Raises:
        CircuitConversionError: If qasm to braket conversion fails

    """
    try:
        program = OpenQasmProgram(source=qasm_str)
        return Circuit.from_ir(source=program.source, inputs=program.inputs)
    except Exception as err:
        raise QasmError("Error converting qasm3 string to braket circuit") from err

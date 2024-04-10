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

from qbraid.programs import QasmError, convert_qasm_pi_to_decimal

QASMType = str


def qasm3_to_braket(qasm3_str: QASMType) -> Circuit:
    """Converts an OpenQASM 3.0 string to a ``braket.circuits.Circuit``.

    Args:
        qasm3_str: OpenQASM 3 string

    Returns:
        The Amazon Braket circuit equivalent to the input OpenQASM 3.0 string

    Raises:
        CircuitConversionError: If qasm to braket conversion fails

    """
    replacements = {
        "cx ": "cnot ",
        "sdg ": "si ",
        "tdg ": "ti ",
        "sx ": "v ",
        "sxdg ": "vi ",
        "p(": "phaseshift(",
        "cp(": "cphaseshift(",
    }

    def replace_commands(qasm, replacements):
        for old, new in replacements.items():
            qasm = qasm.replace(old, new)
        return qasm

    qasm3_str = qasm3_str.replace('include "stdgates.inc";', "")
    qasm3_str = replace_commands(qasm3_str, replacements)
    qasm3_str = convert_qasm_pi_to_decimal(qasm3_str)

    try:
        program = OpenQasmProgram(source=qasm3_str)
        return Circuit.from_ir(source=program.source, inputs=program.inputs)
    except Exception as err:
        raise QasmError("Error converting qasm3 string to braket circuit") from err


def braket_to_qasm3(circuit: Circuit) -> QASMType:
    """Converts a ``braket.circuits.Circuit`` to an OpenQASM 3.0 string.

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

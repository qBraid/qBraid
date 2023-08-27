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
Module for converting Braket circuits to/from OpenQASM

"""

from braket.circuits import Circuit
from braket.circuits.serialization import IRType
from braket.ir.openqasm import Program as OpenQasmProgram

from qbraid.exceptions import QasmError

QASMType = str


def braket_to_qasm(circuit: Circuit) -> QASMType:
    """Converts a `braket.circuits.Circuit` to an OpenQASM 2.0 string.
    *DEPRECATAION NOTICE*: incomplete function.

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
        >>> print(circuit_to_qasm(circuit))
        OPENQASM 2.0;
        include "qelib1.inc";

        qreg q[3];

        h q[0];
        cx q[0],q[1];
        cx q[1],q[2];

    Args:
        circuit: Amazon Braket quantum circuit

    Returns:
        The OpenQASM string equivalent to the circuit

    """
    # A mapping from Amazon Braket gates to QASM gates
    gates = {
        "cnot": "cx",
        "ccnot": "ccx",
        "i": "id",
        "phaseshift": "p",
        "si": "sdg",
        "ti": "tdg",
        "v": "sx",
        "vi": "sxdg",
    }

    # Including the header
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n\n'

    # Initializing the quantum register
    code += "qreg q[" + str(circuit.qubit_count) + "];\n\n"

    circuit_instr = circuit.instructions
    # Building the QASM codelines by applying gates one at a time
    for ins in circuit_instr:
        # Appending the gate name
        if ins.operator.name.lower() not in gates:
            code += ins.operator.name.lower()
        else:
            code += gates[ins.operator.name.lower()]

        # Appending parameters, if any
        try:
            param = "(" + str(ins.operator.angle) + ") "
        except Exception:  # pylint: disable=broad-except
            param = " "
        code += param

        # Appending the gate targets
        targets = [int(q) for q in ins.target]
        code += f"q[{targets[0]}]"
        for t in range(1, len(targets)):
            code += f", q[{targets[t]}]"
        code += ";\n"

    return code


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
        >>> print(circuit_to_qasm3(circuit))
        OPENQASM 3.0;
        bit[3] __bits__;
        qubit[3] __qubits__;
        h __qubits__[0];
        cnot __qubits__[0], __qubits__[1];
        cnot __qubits__[1], __qubits__[2];
        __bits__[0] = measure __qubits__[0];
        __bits__[1] = measure __qubits__[1];
        __bits__[2] = measure __qubits__[2];

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

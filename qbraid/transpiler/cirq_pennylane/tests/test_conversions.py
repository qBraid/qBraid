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
Unit tests for converting Pennylane QuantumTapes to/from OpenQASM 2.0

"""
import pennylane as qml
from pennylane.tape import QuantumTape

from qbraid.transpiler.cirq_pennylane.conversions import from_qasm, to_qasm


def test_to_qasm():
    with QuantumTape() as tape:
        qml.Hadamard(wires=0)
        qml.CNOT(wires=[0, 1])

    qasm_str = to_qasm(tape)

    # Assert that the returned string is in QASM format and includes the Hadamard and CNOT gates
    assert "OPENQASM 2.0;" in qasm_str
    assert "h q[0];" in qasm_str
    assert "cx q[0],q[1];" in qasm_str


def test_from_qasm():
    qasm_str = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    h q[0];
    cx q[0],q[1];
    measure q[0] -> c[0];
    measure q[1] -> c[1];
    """
    tape = from_qasm(qasm_str)

    # Assert that the tape has the correct number of operations
    assert len(tape.operations) == 2

    # Assert that the first operation is a Hadamard gate
    assert isinstance(tape.operations[0], qml.Hadamard)

    # Assert that the second operation is a CNOT gate
    assert isinstance(tape.operations[1], qml.CNOT)


def test_roundtrip_qasm_to_tape_to_qasm():
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
    """
    tape = from_qasm(qasm_str)
    roundtrip_qasm_str = to_qasm(tape)

    print(qasm_str)
    print()
    print(roundtrip_qasm_str)

    # Assert that the original and roundtrip QASM strings are equivalent
    assert qasm_str.strip() == roundtrip_qasm_str.strip()

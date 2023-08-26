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
Unit tests for converting Braket circuits to/from OpenQASM

"""

from braket.circuits import Circuit

from qbraid.interface.qbraid_braket.qasm import braket_from_qasm3, braket_to_qasm3


def test_braket_to_qasm3_bell_circuit():
    """Test converting braket bell circuit to OpenQASM 3.0 string"""
    qasm_expected = """
OPENQASM 3.0;
bit[2] __bits__;
qubit[2] __qubits__;
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];
__bits__[0] = measure __qubits__[0];
__bits__[1] = measure __qubits__[1];
"""
    bell = Circuit().h(0).cnot(0, 1)
    assert qasm_expected.strip("\n") == braket_to_qasm3(bell)


def test_braket_from_qasm3():
    """Test converting OpenQASM 3 string to braket circuit"""
    qasm_str = """"
OPENQASM 3.0;
bit[2] b;
qubit[2] q;
rx(0.15) q[0];
rx(0.3) q[1];
b[0] = measure q[0];
b[1] = measure q[1];
"""
    circuit_expected = Circuit().rx(0, 0.15).rx(1, 0.3)
    assert circuit_expected == braket_from_qasm3(qasm_str)

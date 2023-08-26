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
Unit tests for OpenQASM 2 utility functions.

"""

import pytest

from qbraid.interface.qbraid_qasm.circuits import (
    _read_qasm_file,
    qasm2_bell,
    qasm2_raw_shared15,
    qasm2_shared15,
)
from qbraid.interface.qbraid_qasm.tools import qasm_depth, qasm_num_qubits, qasm_qubits


def test_qasm_qubits():
    """Test getting QASM qubits"""

    assert qasm_qubits(qasm2_bell()) == ["q[0]", "q[1]"]
    assert qasm_qubits(qasm2_shared15()) == ["q[0]", "q[1]", "q[2]", "q[3]"]


def test_qasm_num_qubits():
    """Test calculating number of qubits in qasm2 circuit"""
    assert qasm_num_qubits(qasm2_bell()) == 2
    assert qasm_num_qubits(qasm2_shared15()) == 4


def test_qasm_depth():
    """Test calculating qasm depth of qasm2 circuit"""
    assert qasm_depth(qasm2_bell()) == 2
    assert qasm_depth(qasm2_shared15()) == 7
    assert qasm_depth(qasm2_raw_shared15()) == 22


def test_qasm_depth_barrier():
    qasm_barrier_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
barrier q;
h q[1];"""
    assert qasm_depth(qasm_barrier_str) == 2


def test_qasm_depth_qubit_plus_gate_alias():
    qasm_str = """OPENQASM 2.0;
include "qelib1.inc";
gate majority a,b,c
{
cx c,b;
cx c,a;
ccx a,b,c;
}
gate unmaj a,b,c
{
ccx a,b,c;
cx c,a;
cx a,b;
}
qreg cin[1];
qreg a[4];
qreg b[4];
qreg cout[1];
creg ans[5];
// set input states
x a[0]; // a = 0001
x b; // b = 1111
// add a to b, storing result in b
majority cin[0],b[0],a[0];
majority a[0],b[1],a[1];
majority a[1],b[2],a[2];
majority a[2],b[3],a[3];
cx a[3],cout[0];
unmaj a[2],b[3],a[3];
unmaj a[1],b[2],a[2];
unmaj a[0],b[1],a[1];
unmaj cin[0],b[0],a[0];
measure b[0] -> ans[0];
measure b[1] -> ans[1];
measure b[2] -> ans[2];
measure b[3] -> ans[3];
measure cout[0] -> ans[4];
"""
    assert qasm_depth(qasm_str) == 11


@pytest.mark.parametrize(
    "qasm_str, expected_depth",
    [
        (
            """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c0[1];
creg c1[1];
h q[0];
h q[1];
measure q[0] -> c0[0];
if(c0==0) x q[1];""",
            3,
        ),
        (
            """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c0[1];
creg c1[1];
h q;
measure q[0] -> c0[0];
if(c0==0) x q[1];
if(c0==0) measure q[1] -> c1[0];""",
            4,
        ),
    ],
)
def test_qasm_depth_if_statement(qasm_str, expected_depth):
    """Test calculating qasm depth with program containing if statement"""
    assert qasm_depth(qasm_str) == expected_depth


def test_qasm_depth_qtp():
    qasm_qtp_str = _read_qasm_file("qtp.qasm")
    assert qasm_depth(qasm_qtp_str) == 9

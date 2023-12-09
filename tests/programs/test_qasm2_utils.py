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

from qbraid import circuit_wrapper

from .._data.qasm2.circuits import _read_qasm_file, qasm2_bell, qasm2_cirq_shared15, qasm2_shared15


def test_qasm_qubits():
    """Test getting QASM qubits"""

    assert circuit_wrapper(qasm2_bell()).qubits == ["q[0]", "q[1]"]
    assert circuit_wrapper(qasm2_shared15()).qubits == ["q[0]", "q[1]", "q[2]", "q[3]"]


def test_qasm_num_qubits():
    """Test calculating number of qubits in qasm2 circuit"""
    assert circuit_wrapper(qasm2_bell()).num_qubits == 2
    assert circuit_wrapper(qasm2_shared15()).num_qubits == 4


QASM_DEPTH_DATA = [
    (qasm2_bell(), 2),
    (qasm2_shared15(), 7),
    (qasm2_cirq_shared15(), 22),
    (_read_qasm_file("qtp.qasm"), 9),
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
barrier q;
h q[1];
        """,
        2,
    ),
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
if(c0==0) x q[1];
        """,
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
if(c0==0) measure q[1] -> c1[0];
        """,
        4,
    ),
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
qreg a[2];
creg c[3];
creg syn[2];
gate syndrome d1,d2,d3,a1,a2
{
cx d1,a1; cx d2,a1;
cx d2,a2; cx d3,a2;
}
x q[0];
barrier q;
syndrome q[0],q[1],q[2],a[0],a[1];
measure a -> syn;
if(syn==1) x q[0];
if(syn==2) x q[2];
if(syn==3) x q[1];
measure q -> c;
        """,
        7,
    ),
    (
        """
OPENQASM 2.0;
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
x a[0];
x b;
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
        """,
        11,
    ),
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
creg c[4];
h q;
barrier q;
h q[0];
measure q[0] -> c[0];
if(c==1) u1(pi/2) q[1];
h q[1];
measure q[1] -> c[1];
if(c==1) u1(pi/4) q[2];
if(c==2) u1(pi/2) q[2];
if(c==3) u1(pi/2+pi/4) q[2];
h q[2];
measure q[2] -> c[2];
if(c==1) u1(pi/8) q[3];
if(c==2) u1(pi/4) q[3];
if(c==3) u1(pi/4+pi/8) q[3];
if(c==4) u1(pi/2) q[3];
if(c==5) u1(pi/2+pi/8) q[3];
if(c==6) u1(pi/2+pi/4) q[3];
if(c==7) u1(pi/2+pi/4+pi/8) q[3];
h q[3];
measure q[3] -> c[3];
        """,
        20,
    ),
]


@pytest.mark.parametrize("qasm_str, expected_depth", QASM_DEPTH_DATA)
def test_qasm_depth(qasm_str, expected_depth):
    """Test calculating depth of circuit represented by qasm2 string"""
    qprogram = circuit_wrapper(qasm_str)
    assert qprogram.depth == expected_depth

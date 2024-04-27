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
Unit tests for QASM preprocessing functions

"""
import pytest

from qbraid.transforms.qasm2.passes import (
    convert_qasm_pi_to_decimal,
    flatten_qasm_program,
    remove_qasm_barriers,
)

pi_decimal_data = [
    (
        """
        OPENQASM 3;
        qubit[1] q;
        h q[0];
        rx(pi / 4) q[0];
        ry(2*pi) q[0];
        rz(3 * pi/4) q[0];
        """,
        """
        OPENQASM 3;
        qubit[1] q;
        h q[0];
        rx(0.7853981633974483) q[0];
        ry(6.283185307179586) q[0];
        rz(2.356194490192345) q[0];
        """,
    ),
]


def strings_equal(s1, s2):
    """Check if two strings are equal, ignoring spaces and newlines."""
    s1_clean = s1.replace(" ", "").replace("\n", "")
    s2_clean = s2.replace(" ", "").replace("\n", "")
    return s1_clean == s2_clean


@pytest.mark.parametrize("qasm3_str_pi, qasm3_str_decimal", pi_decimal_data)
def test_convert_pi_to_decimal(qasm3_str_pi, qasm3_str_decimal):
    """Test converting pi symbol to decimal in qasm3 string"""
    assert convert_qasm_pi_to_decimal(qasm3_str_pi) == qasm3_str_decimal


def test_remove_qasm_barriers():
    """Test removing qasm barriers"""
    assert (
        remove_qasm_barriers(
            """
// quantum ripple-carry adder from Cuccaro et al, quant-ph/0410184
OPENQASM 2.0;
include "qelib1.inc";
include "barrier.inc";
include ";barrier.inc";
gate majority a,b,c
{
  cx c,b;
  cx c,a;
  ccx a,b,c;
}
gate barrier1 a,a,a,a,a{
    barrier x,y,z;
    barrier1;
    barrier;
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
// barrier;
qreg cout[1]; barrier x,y,z;
creg ans[5];
// set input states
x a[0]; // a = 0001
x b;    // b = 1111
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
// quantum ripple-carry adder from Cuccaro et al, quant-ph/0410184
"""
        )
        == """
// quantum ripple-carry adder from Cuccaro et al, quant-ph/0410184
OPENQASM 2.0;
include "qelib1.inc";
include "barrier.inc";
include ";barrier.inc";
gate majority a,b,c
{
  cx c,b;
  cx c,a;
  ccx a,b,c;
}
gate barrier1 a,a,a,a,a{
    barrier1;
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
// barrier;
qreg cout[1];
creg ans[5];
// set input states
x a[0]; // a = 0001
x b;    // b = 1111
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
// quantum ripple-carry adder from Cuccaro et al, quant-ph/0410184
"""
    )


def test_convert_qasm_one_param():
    """Test converting qasm string from one-parameter gate"""

    qasm_in = """
OPENQASM 2.0;
include "qelib1.inc";
gate ryy(param0) q0,q1 { rx(pi/2) q0; rx(pi/2) q1; cx q0,q1; rz(param0) q1; cx q0,q1; rx(-pi/2) q0; rx(-pi/2) q1; }
qreg q[2];
ryy(2.0425171585294746) q[1],q[0];
"""
    expected_out = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
rx(pi/2) q[1];
rx(pi/2) q[0];
cx q[1],q[0];
rz(2.0425171585294746) q[0];
cx q[1],q[0];
rx(-pi/2) q[1];
rx(-pi/2) q[0];
"""
    qasm_out = flatten_qasm_program(qasm_in)
    assert strings_equal(qasm_out, expected_out)


def test_convert_qasm_two_param():
    """Test converting qasm string from two-parameter gate"""

    qasm_in = """
OPENQASM 2.0;
include "qelib1.inc";
gate xx_minus_yy(param0,param1) q0,q1 { rz(-1.0*param1) q1; ry(param0/2) q0; }
qreg q[2];
xx_minus_yy(2.00367210595874,5.07865952845335) q[0],q[1];
"""
    expected_out = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
rz(-1.0*5.07865952845335) q[1];
ry(2.00367210595874/2) q[0];
"""
    qasm_out = flatten_qasm_program(qasm_in)
    assert strings_equal(qasm_out, expected_out)


def test_convert_qasm_three_qubit_gate():
    """Test converting qasm string that uses three qubit gate"""

    qasm_in = """
OPENQASM 2.0;
include "qelib1.inc";
gate ryy(param0) q0,q1,q2 { rx(pi/2) q0; rx(pi/2) q1; cx q0,q2; rz(param0) q1; cx q0,q1; rx(-pi/2) q2; rx(-pi/2) q1; }
qreg q[3];
ryy(2.0425171585294746) q[1],q[0],q[2];
"""
    expected_out = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
rx(pi/2) q[1];
rx(pi/2) q[0];
cx q[1],q[2];
rz(2.0425171585294746) q[0];
cx q[1],q[0];
rx(-pi/2) q[2];
rx(-pi/2) q[0];
"""
    qasm_out = flatten_qasm_program(qasm_in)
    assert strings_equal(qasm_out, expected_out)


def test_convert_qasm_non_param_gate_def():
    """Test converting qasm string from non-parameterized gate def"""

    qasm_in = """
OPENQASM 2.0;
include "qelib1.inc";
gate ecr q0,q1 { rzx(pi/4) q0,q1; x q0; rzx(-pi/4) q0,q1; }
qreg q[2];
ecr q[0],q[1];
"""
    expected_out = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
rzx(pi/4) q[0],q[1];
x q[0];
rzx(-pi/4) q[0],q[1];
"""
    qasm_out = flatten_qasm_program(qasm_in)
    assert strings_equal(qasm_out, expected_out)


def test_convert_qasm_recursive_gate_def():
    """Test converting qasm string from gate defined in terms of another gate"""

    qasm_in = """
OPENQASM 2.0;
include "qelib1.inc";
gate rzx(param0) q0,q1 { h q1; cx q0,q1; rz(param0) q1; cx q0,q1; h q1; }
gate ecr q0,q1 { rzx(pi/4) q0,q1; x q0; rzx(-pi/4) q0,q1; }
qreg q[2];
ecr q[0],q[1];
"""
    expected_out = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[1];
cx q[0],q[1];
rz(pi/4) q[1];
cx q[0],q[1];
h q[1];
x q[0];
h q[1];
cx q[0],q[1];
rz(-pi/4) q[1];
cx q[0],q[1];
h q[1];
"""
    qasm_out = flatten_qasm_program(qasm_in)
    assert strings_equal(qasm_out, expected_out)

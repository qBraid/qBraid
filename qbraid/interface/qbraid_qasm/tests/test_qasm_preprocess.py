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

from qbraid.interface.qbraid_qasm.qasm_preprocess import _remove_barriers, convert_to_supported_qasm

qasm_0 = """OPENQASM 2.0;
include "qelib1.inc";
gate rzx(param0) q0,q1 { h q1; cx q0,q1; rz(-pi/4) q1; cx q0,q1; h q1; }
gate ecr q0,q1 { rzx(pi/4) q0,q1; x q0; rzx(-pi/4) q0,q1; }
gate rzx_6320157840(param0) q0,q1 { h q1; cx q0,q1; rz(2.3200048200765524) q1; cx q0,q1; h q1; }
qreg q[4];
cry(5.518945082555831) q[0],q[1];
u(5.75740842861076,5.870881397684582,1.8535618384181967) q[2];
ecr q[3],q[0];
rzx_6320157840(2.3200048200765524) q[2],q[1];
rccx q[1],q[2],q[3];
csx q[0],q[1];
rxx(5.603791034636421) q[2],q[0];
"""

qasm_1 = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[5];
rccx q[1],q[2],q[0];
cu(5.64,3.60,3.73, 5.68) q[1],q[0];
c3x q[1],q[3],q[0],q[2];
c3sqrtx q[3],q[1],q[2],q[0];
c4x q[2],q[0],q[1],q[4],q[3];
rc3x q[1],q[2],q[0],q[3];
"""

qasm_lst = [qasm_0, qasm_1]


def strings_equal(s1, s2):
    """Check if two strings are equal, ignoring spaces and newlines."""
    s1_clean = s1.replace(" ", "").replace("\n", "")
    s2_clean = s2.replace(" ", "").replace("\n", "")
    return s1_clean == s2_clean


def test_remove_qasm_barriers():
    """Test removing qasm barriers"""
    assert (
        _remove_barriers(
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
    qasm_out = convert_to_supported_qasm(qasm_in)
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
    qasm_out = convert_to_supported_qasm(qasm_in)
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
    qasm_out = convert_to_supported_qasm(qasm_in)
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
    qasm_out = convert_to_supported_qasm(qasm_in)
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
    qasm_out = convert_to_supported_qasm(qasm_in)
    assert strings_equal(qasm_out, expected_out)

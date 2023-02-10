# Copyright 2021 The Cirq Developers
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

"""
Unit tests for qasm utility functions

"""

from qbraid.transpiler.cirq_qasm.qasm_conversions import _remove_qasm_barriers


def test_remove_qasm_barriers():
    assert (
        _remove_qasm_barriers(
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

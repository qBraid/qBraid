OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
h q[1];
cx q[1], q[0];
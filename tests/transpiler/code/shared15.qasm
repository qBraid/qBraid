// Generated from Cirq v1.1.0

OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q(0), q(1), q(2), q(3)]
qreg q[4];


h q[3];
h q[2];
h q[1];
h q[0];
x q[3];
x q[2];
y q[1];
z q[0];
s q[3];
sdg q[2];
t q[1];
tdg q[0];
rx(pi*0.25) q[3];
ry(pi*0.5) q[2];
rz(pi*0.75) q[1];
rz(pi*0.125) q[0];
sx q[3];
sxdg q[2];

// Gate: ISWAP
cx q[1],q[0];
h q[1];
cx q[0],q[1];
s q[1];
cx q[0],q[1];
sdg q[1];
h q[1];
cx q[1],q[0];

swap q[3],q[1];
swap q[2],q[0];
cx q[3],q[2];

// Gate: CZ**0.25
u3(pi*0.5,pi*1.0,pi*0.25) q[1];
u3(pi*0.5,pi*1.0,pi*0.75) q[0];
sx q[1];
cx q[1],q[0];
rx(pi*0.375) q[1];
ry(pi*0.5) q[0];
cx q[0],q[1];
sxdg q[0];
s q[0];
cx q[1],q[0];
u3(pi*0.5,pi*0.875,0) q[1];
u3(pi*0.5,pi*0.375,0) q[0];

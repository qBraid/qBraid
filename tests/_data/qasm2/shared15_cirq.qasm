OPENQASM 2.0;
include "qelib1.inc";

// Qubits: [q(0), q(1), q(2), q(3)]
qreg q[4];

h q[0];
h q[1];
h q[2];
h q[3];
x q[0];
x q[1];
y q[2];
z q[3];
s q[0];
sdg q[1];
t q[2];
tdg q[3];
rx(pi*0.25) q[0];
ry(pi*0.5) q[1];
rz(pi*0.75) q[2];
rz(pi*0.125) q[3];
sx q[0];
sxdg q[1];

// Gate: ISWAP
cx q[2],q[3];
h q[2];
cx q[3],q[2];
s q[2];
cx q[3],q[2];
sdg q[2];
h q[2];
cx q[2],q[3];

swap q[0],q[2];
swap q[1],q[3];
cx q[0],q[1];

// Gate: CZ**0.25
u3(pi*0.5,pi*1.0,pi*0.25) q[2];
u3(pi*0.5,pi*1.0,pi*0.75) q[3];
sx q[2];
cx q[2],q[3];
rx(pi*0.375) q[2];
ry(pi*0.5) q[3];
cx q[3],q[2];
sxdg q[3];
s q[3];
cx q[2],q[3];
u3(pi*0.5,pi*0.875,0) q[2];
u3(pi*0.5,pi*0.375,0) q[3];
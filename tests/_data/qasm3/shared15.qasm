OPENQASM 3;
include "stdgates.inc";
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
}
qubit[4] q;
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
rx(pi/4) q[0];
ry(pi/2) q[1];
rz(3*pi/4) q[2];
p(pi/8) q[3];
sx q[0];
sxdg q[1];
iswap q[2], q[3];
swap q[0], q[2];
swap q[1], q[3];
cx q[0], q[1];
cp(pi/4) q[2], q[3];
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
rx(pi/4) q[3];
ry(pi/2) q[2];
rz(3*pi/4) q[1];
p(pi/8) q[0];
sx q[3];
sxdg q[2];
iswap q[1], q[0];
swap q[3], q[1];
swap q[2], q[0];
cx q[3], q[2];
cp(pi/4) q[1], q[0];
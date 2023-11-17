gate cnot c, t {
  CX c, t;
}

// Iswap
gate iswap a, b {
  s a; 
  s b;
  h a; 
  cnot a, b;
  cnot b, a; 
  h b;
}

// what are the gates which qiskit and braket consider to be "standard"? 

// add both of their definitions, so that we can use them in the circuit

// U is not used in Braket but is used in Qiskit 
// there is no definition for it in their std library (but it should be a native gate???)


// Braket ref : https://github.com/amazon-braket/amazon-braket-default-simulator-python/blob/main/src/braket/default_simulator/openqasm/braket_gates.inc

// Clifford gate: inverse of sqrt(Z)
gate si a { inv @ pow(1/2) @ z a; }

// inverse of sqrt(S)
gate ti a { inv @ pow(1/2) @ s a; }

// sqrt(NOT) gate
gate v a { pow(1/2) @ x a; }

// inverse of sqrt(NOT)
gate vi a { inv @ pow(1/2) @ x a; }

// Ising gates
gate xx(θ) a, b {
  h a; h b;
  cnot a, b;
  rz(θ) b;
  cnot a, b;
  h a; h b;
}
gate yy(θ) a, b {
  rx(π/2) a; rx(π/2) b;
  cnot a, b;
  rz(θ) b;
  cnot a, b;
  rx(-π/2) a; rx(-π/2) b;
}
gate zz(θ) a, b {
  cnot a, b;
  rz(θ) b;
  cnot a, b;
}
gate xy(θ) a, b {
  h a;
  cy a, b;
  ry(θ/2) a;
  rx(-θ/2) b;
  cy a, b;
  h a;
}
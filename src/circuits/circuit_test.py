from typing import Union
from circuit import Circuit

from qubit import Qubit

import cirq
from cirq.circuits import Circuit as CirqCircuit
from cirq.ops.gate_features import SingleQubitGate as CirqSingleQubitGate
from cirq.ops.gate_features import TwoQubitGate as CirqTwoQubitGate
from cirq.ops.gate_features import ThreeQubitGate as CirqThreeQubitGate
from cirq.ops.moment import Moment as CirqMoment
from cirq.ops.gate_operation import GateOperation as CirqGateInstruction


import qiskit
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from qiskit.circuit import Instruction as QiskitInstruction
from qiskit.circuit import QuantumRegister as QiskitQuantumRegister
from qiskit.circuit import Gate as QiskitGate

#cirq_gate_types = Union[CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate] 
cirq_gate_types = (CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate)

def cirq_test():
    
    #q0 = cirq.NamedQubit('source')
    #q1 = cirq.NamedQubit('target')   
    #q2 = cirq.LineQubit(0)
    #q3 = cirq.GridQubit(0,3)
     
    q0 = cirq.LineQubit(0)
    q1 = cirq.LineQubit(1)
    
    op_h = cirq.H(q0)
    op_cnot = cirq.CNOT(q0,q1)

    
    circuit = cirq.Circuit()
    
    circuit.append(op_h)
    circuit.append(op_cnot)
    
    test = Circuit(circuit).output('qiskit')
    print(test)
    
    #print(dir(q2))
    #print(q2.x)
    #print(dir(q0))
    #print(q1.name)
    #print(q0.name)
    #print(dir(q3))
    #print(q3.row, q3.col)
    
# =============================================================================
#     moments = circuit.moments
#     operations = moments[1].operations
#     op = operations[0]
# =============================================================================


def qiskit_test():
    
    qubits = QiskitQuantumRegister(3)
    print(qubits[0])
    
    #my_gate = QiskitGate(2,)
    
    circuit = QiskitCircuit(qubits)
    #circuit.qubits
    
    circuit.h(0)
    
    from qiskit.circuit.library.standard_gates.h import HGate
    circuit.append(HGate(),[0],[])
    
    #circuit.x(1)
    circuit.cnot(0,1)
    circuit.h(2)
    circuit.h(0)
    circuit.cnot(1,2)
    
    circuit_qubit_list = circuit.qubits
    circuit_clbit_list = circuit.clbits
    
    
    
    #test = Circuit(circuit)
    #out = test.output('cirq')
    #print(out)
    
def cirq_to_qiskit():
    
    #define qubits
    q0 = cirq.LineQubit(0)
    q1 = cirq.LineQubit(1)
    
    #define operations
    op_h = cirq.H(q0)
    op_cnot = cirq.CNOT(q0,q1)
    op_z = cirq.Z(q1)
    op_t = cirq.T(q0)
    op_s = cirq.S(q1)

    #create circuit
    circuit = cirq.Circuit()
    circuit.append(op_h)
    circuit.append(op_cnot)
    circuit.append(op_z)
    circuit.append(op_s)
    circuit.append(op_t)
    
    #transpile
    qiskit_circuit = Circuit(circuit).output('qiskit')
    print(qiskit_circuit)
    
def qiskit_to_cirq():
    
    #define quantumregister
    qubits = QiskitQuantumRegister(3)
    
    #create circuit
    circuit = QiskitCircuit(qubits)
    circuit.cnot(0,1)
    circuit.h(2)
    circuit.h(0)
    circuit.cnot(1,2)
    circuit.z(1)
    circuit.s(2)
    circuit.h(0)
    circuit.t(1)
    circuit.t(2)
    
    #transpile
    cirq_circuit = Circuit(circuit).output('cirq')
    print(cirq_circuit)
    
    
if __name__ == "__main__":
    
    cirq_to_qiskit()
    qiskit_to_cirq()
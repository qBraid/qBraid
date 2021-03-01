from typing import Union
from circuit import Circuit

import numpy as np

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

from braket.circuits import Circuit as BraketCircuit
from braket.circuits.qubit import Qubit as BraketQubit
from braket.circuits.qubit_set import QubitSet as BraketQubitSet
from braket.circuits.gate import Gate as BraketGate
from braket.circuits.instruction import Instruction as BraketInstruction


#cirq_gate_types = Union[CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate] 
cirq_gate_types = (CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate)

    
def braket_to_all():
    
    circuit = BraketCircuit()
    bell = circuit.h(0).cnot(control=0,target=1)
    
    circuit = BraketCircuit().h(range(4)).cnot(control=0, target=2).cnot(control=1, target=3)
    
    qbraid_circuit = Circuit(circuit)
    cirq_circuit = qbraid_circuit.output('cirq')
    print(cirq_circuit)
    qiskit_circuit = qbraid_circuit.output('qiskit')
    print(qiskit_circuit)
    
    
def cirq_to_all():
    
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
    qbraid_circuit = Circuit(circuit)
    qiskit_circuit = qbraid_circuit.output('qiskit')
    print(qiskit_circuit)
    braket_circuit = qbraid_circuit.output('braket')
    print(braket_circuit)
    
def qiskit_to_all():
    
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
    circuit.rx(np.pi/3,0)
    
    #transpile
    
    qbraid_circuit = Circuit(circuit)
    cirq_circuit = qbraid_circuit.output('cirq')
    print(cirq_circuit)
    braket_circuit = qbraid_circuit.output('braket')
    print(braket_circuit)
    

def cirq_test():
    
    #cirq
    #define qubits
    q0 = cirq.LineQubit(0)
    q1 = cirq.LineQubit(1)
    
    circuit = CirqCircuit()
    theta=np.pi/2
    rz_gate = cirq.rz(theta)
    circuit.append(rz_gate(q0))
    circuit.append(rz_gate(q1))
    
    print(dir(rz_gate))
    print(rz_gate.exponent)
    print(rz_gate.global_shift)
    print(rz_gate.with_canonical_global_phase().global_shift)
    
    
def qiskit_test():
    
    #circuit = QiskitQuantumCircuit(2,2)
    
    #circuit.rz(0,)
    
    from qiskit.circuit.library.standard_gates.x import CXGate as QiskitCXGate
    from qiskit.circuit import ControlledGate as QiskitControlledGate
    from qiskit.circuit.library.standard_gates.rx import CRXGate as QiskitCRXGate
    from qiskit.circuit.library.standard_gates.u3 import U3Gate
    cx = QiskitCXGate()
    print(isinstance(cx,QiskitControlledGate))
    print(cx.num_ctrl_qubits)
    print(cx.num_clbits)
    
    cx2 = cx.control(2)
    print(cx2.num_ctrl_qubits)    
    
    crx = QiskitCRXGate(np.pi/2)
    print(crx.name)
    print(crx.params)
    print(crx.num_qubits)
    
    u3 = U3Gate(np.pi/2,np.pi,np.pi/4)
    print(u3.params)
    print(u3.name)
    

if __name__ == "__main__":
    
    #cirq_test()
    qiskit_test()
    
    
    #braket_to_all()
    #cirq_to_all()
    qiskit_to_all()
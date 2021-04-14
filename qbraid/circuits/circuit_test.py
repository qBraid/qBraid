from typing import Union
import numpy as np
from numpy import pi
from sympy import Symbol

from qbraid.circuits.transpiler import qbraid_wrapper

from qiskit.circuit import Parameter


import cirq
from cirq.circuits import Circuit as CirqCircuit
from cirq.ops.gate_features import SingleQubitGate as CirqSingleQubitGate
from cirq.ops.gate_features import TwoQubitGate as CirqTwoQubitGate
from cirq.ops.gate_features import ThreeQubitGate as CirqThreeQubitGate
from cirq.ops.moment import Moment as CirqMoment
from cirq.ops.gate_operation import GateOperation as CirqGateInstruction
from cirq.ops.controlled_gate import ControlledGate
from cirq import ControlledGate

import qiskit
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from qiskit.circuit import Instruction as QiskitInstruction
from qiskit.circuit import QuantumRegister as QiskitQuantumRegister
from qiskit.circuit.classicalregister import ClassicalRegister as QiskitClassicalRegister
from qiskit.circuit import Gate as QiskitGate
from qiskit.circuit import Parameter as QiskitParameter

from braket.circuits import Circuit as BraketCircuit
from braket.circuits.qubit import Qubit as BraketQubit
from braket.circuits.qubit_set import QubitSet as BraketQubitSet
from braket.circuits.gate import Gate as BraketGate
from braket.circuits.instruction import Instruction as BraketInstruction


#cirq_gate_types = Union[CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate] 
cirq_gate_types = (CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate)

    
def braket_to_all():
    
    circuit = BraketCircuit()
    #bell = circuit.h(0).cnot(control=0,target=1)
    
    instructions = []
    instructions.append(BraketInstruction(BraketGate.H() ,0 ))
    instructions.append(BraketInstruction(BraketGate.X() , 1))
    instructions.append(BraketInstruction(BraketGate.Y() , 2))
    instructions.append(BraketInstruction(BraketGate.Z() , 1))
    instructions.append(BraketInstruction(BraketGate.S() , 0))
    instructions.append(BraketInstruction(BraketGate.Si() ,1 ))
    instructions.append(BraketInstruction(BraketGate.T() , 2))
    instructions.append(BraketInstruction(BraketGate.Ti() ,1 ))
    instructions.append(BraketInstruction(BraketGate.I() , 0))
    instructions.append(BraketInstruction(BraketGate.V() , 0))
    instructions.append(BraketInstruction(BraketGate.Vi() ,2 ))
    instructions.append(BraketInstruction(BraketGate.PhaseShift(pi),2 ))
    instructions.append(BraketInstruction(BraketGate.Rx(pi) ,0 ))
    instructions.append(BraketInstruction(BraketGate.Ry(pi) ,1 ))
    instructions.append(BraketInstruction(BraketGate.Rz(pi/2) ,2 ))
    instructions.append(BraketInstruction(BraketGate.CNot() ,[1,0] ))
    instructions.append(BraketInstruction(BraketGate.Swap() ,[1,2] ))
    instructions.append(BraketInstruction(BraketGate.ISwap() ,[1,2] ))
    instructions.append(BraketInstruction(BraketGate.PSwap(pi) ,[0,1] ))
    instructions.append(BraketInstruction(BraketGate.CY() , [0,1]))
    instructions.append(BraketInstruction(BraketGate.CZ() , [1,0]))
    instructions.append(BraketInstruction(BraketGate.CPhaseShift(pi/4) ,[2,0] ))
    instructions.append(BraketInstruction(BraketGate.XX(pi) ,[0,1] ))
    instructions.append(BraketInstruction(BraketGate.XY(pi) ,[0,1] ))
    instructions.append(BraketInstruction(BraketGate.YY(pi) ,[0,1] ))
    instructions.append(BraketInstruction(BraketGate.ZZ(pi) ,[0,1] ))
    instructions.append(BraketInstruction(BraketGate.CCNot() ,[0,1,2] ))
    
    for inst in instructions:
        circuit.add_instruction(inst)    
    
    print(circuit)
    qbraid_circuit = qbraid_wrapper(circuit)
    
    cirq_circuit = qbraid_circuit.transpile(package = 'cirq')
    print(cirq_circuit)
    qiskit_circuit = qbraid_circuit.transpile('qiskit') #, auto_measure = True)
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

    # add operations to circuit
    circuit = cirq.Circuit()
    circuit.append(op_h)
    circuit.append(op_cnot)
    circuit.append(op_z)
    circuit.append(op_s)
    circuit.append(op_t)
    
    # measure both qubits
    m0 = cirq.measure(q0, key=0)
    m1 = cirq.measure(q1, key=1)
    circuit.append([m0,m1])
    
    # transpile
    qbraid_circuit = qbraid_wrapper(circuit)
    
    print("cirq circuit\n\n", circuit)
    qiskit_circuit = qbraid_circuit.transpile('qiskit')
    print("qiskit circuit\n\n", qiskit_circuit)
    braket_circuit = qbraid_circuit.transpile('braket')
    print("braket circuit\n\n", braket_circuit)
    
def qiskit_to_all():
    
    #define quantumregister
    qubits = QiskitQuantumRegister(3)
    clbits = QiskitClassicalRegister(3)
    
    #create circuit
    circuit = QiskitCircuit(qubits,clbits)
    circuit.cnot(0,1)
    circuit.h(2)
    circuit.h(0)
    circuit.cnot(1,2)
    circuit.z(1)
    circuit.s(2)
    circuit.h(0)
    circuit.t(1)
    circuit.t(2)
    #circuit.rx(np.pi/3,0)
    circuit.measure([0,1,2],[2,1,0])
    print(circuit)
    
    #transpile
    qbraid_circuit = qbraid_wrapper(circuit)
    cirq_circuit = qbraid_circuit.transpile('cirq')
    print("cirq ciruit")
    print(cirq_circuit)
    
    #simulate cirq circuit
    #from cirq import Simulator
    #simulator = Simulator()
    #result = simulator.run(cirq_circuit)
    #print(result)
    
    braket_circuit = qbraid_circuit.transpile('braket')
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
    
    circuit.append(cirq.H(q0))
    circuit.append(cirq.CNOT(q0,q1))
    
    
    m0 = cirq.measure(q0, key=0)
    m1 = cirq.measure(q1, key=1)
    
    
    
    circuit.append([m0,m1])
    
    print(circuit)
    
    from cirq import Simulator
    simulator = Simulator()
    result = simulator.run(circuit)
    print(result)
    
    #Circuit(circuit)
    
def qiskit_test():
    
    #circuit = QiskitQuantumCircuit(2,2)
    
    #circuit.rz(0,)
    
    from qiskit.circuit.library.standard_gates.x import CXGate as QiskitCXGate
    from qiskit.circuit import ControlledGate as QiskitControlledGate
    from qiskit.circuit.library.standard_gates.rx import CRXGate as QiskitCRXGate
    from qiskit.circuit.library.standard_gates.u3 import U3Gate
    from qiskit.circuit.measure import Measure as QiskitMeasure
    
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
    
    measure = QiskitMeasure()
    
    circuit = QiskitCircuit(2,4)
    circuit.h(0)
    circuit.cnot(0,1)
    circuit.measure([0],[0])
    circuit.measure([1],[1])
    #circuit.measure([0,1],[3,2])
    
    #Circuit(circuit)
    print(circuit.clbits)
    
    for instruction, qubit_list, clbit_list in circuit.data:

        if isinstance(instruction,QiskitMeasure):
            print(instruction, qubit_list, clbit_list)
            print(clbit_list[0].index)
            print(dir(clbit_list[0]))
            break
    
    #Circuit(circuit)
    #define quantumregister
    qubits = QiskitQuantumRegister(3)
    clbits = QiskitClassicalRegister(3)
    
    #create circuit
    circuit = QiskitCircuit(qubits,clbits)
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
    circuit.measure([0,1,2],[2,1,0])
    
    for instruction, qubit_list, clbit_list in circuit.data:
        if isinstance(instruction,QiskitMeasure):
            print(dir(instruction))

def braket_test():
    
    circuit = BraketCircuit().h(range(4)).cnot(control=0, target=2).cnot(control=1, target=3)
    
    for instruction in circuit.instructions:
        print(instruction)

def test_function():
    
    #define qubits
    q0 = cirq.LineQubit(0)
    q1 = cirq.LineQubit(1)
    
    #define operations
    op_h = cirq.H(q0)**1.8
    op_cnot = cirq.CNOT(q0,q1)
    op_z = cirq.Z(q1)
    op_t = cirq.T(q0)
    op_s = cirq.S(q1)

    h = cirq.H.controlled(1)
    op_controlled_h = h(q0,q1)

    # add operations to circuit
    circuit = cirq.Circuit()
    circuit.append(op_h)
    circuit.append(cirq.H(q0))
    circuit.append(cirq.X(q1))
    circuit.append(op_cnot)
    circuit.append(op_z)
    circuit.append(op_s)
    circuit.append(op_t)
    circuit.append(op_controlled_h)
    
    # measure both qubits
    m0 = cirq.measure(q0, key=0)
    m1 = cirq.measure(q1, key=1)
    circuit.append([m0,m1])
    
    # transpile
    qbraid_circuit = qbraid_wrapper(circuit)
    
    print("cirq circuit\n")
    print(circuit)
    qiskit_circuit = qbraid_circuit.transpile('qiskit')
    print("qiskit circuit\n")
    print(qiskit_circuit)
    
    cirq_circuit_2 = qbraid_wrapper(qiskit_circuit).transpile('cirq')
    print("cirq circuit 2")
    print(cirq_circuit_2)
    
    print(circuit == cirq_circuit_2)


def test_qiskit_parameters():
    
    #from qiskit.circuit import Parameter

    theta = Parameter('θ')
    
    n = 5
    
    qc = QiskitCircuit(5, 1)
    
    qc.rz(pi/4, range(5))
    
    qc.h(0)
    for i in range(n-1):
        qc.cx(i, i+1)
    
    qc.barrier()
    qc.rz(theta, range(2,5))
    qc.barrier()
    
    for i in reversed(range(n-1)):
        qc.cx(i, i+1)
    qc.h(0)
    qc.measure(0, 0)
    
    print(qc)
    #print(dir(qc.parameters))
    #print(list(qc.parameters))
    
    for instruction, qubit_list, clbit_list in qc.data:
        print(instruction.params)

def test_parametrized_circuit():
    
    #qc = QiskitCircuit(1,1)
    #qc.rz(QiskitParameter('x'),0)
    #qc.rz(QiskitParameter('y'),0)
    
    theta = Parameter('θ')
    
    n = 5
    
    qc = QiskitCircuit(5, 1)
    
    #qc.rz(pi/4, [0,1,2])
    
    qc.h(0)
    for i in range(n-1):
        qc.cx(i, i+1)
    
    #qc.barrier()
    qc.rz(theta, range(5))
    #qc.barrier()
    
    for i in reversed(range(n-1)):
        qc.cx(i, i+1)
    qc.h(0)
    qc.measure(0, 0)
    
    #qc.draw('mpl')
    print(qc)
    qbraid_circuit = qbraid_wrapper(qc)
    cqc = qbraid_circuit.transpile('cirq')
    #for op in cqc.all_operations():
    #    print(type(op.gate.exponent))
    print(cqc)
    

if __name__ == "__main__":
    
    #test_qiskit_parameters()
    test_parametrized_circuit()
    

    #from qbraid.circuits.cirq_gates import cirq_gates
    #print(cirq_gates)

    #test_function()
    
    
    #cirq_test()
    #qiskit_test()
    #braket_test()
    
    #braket_to_all()
    #cirq_to_all()
    #qiskit_to_all()
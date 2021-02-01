import copy

from circuits.qubit import qB_Qubit
from circuits.qubitset import qB_QubitSet
from circuits.gate import qB_Gate
from circuits.instruction import qB_Instruction
from circuits.moment import qB_Moment
from circuits.circuit import qB_Circuit

from braket.circuits.qubit import Qubit as aws_Qubit
from braket.circuits.qubit_set import  QubitSet as aws_QubitSet
from braket.circuits.gate import Gate as aws_Gate
from braket.circuits.instruction import Instruction as aws_Instruction
from braket.circuits.moments import Moments as aws_Moments
from braket.circuits.circuit import Circuit as aws_Circuit

from cirq.ops.named_qubit import NamedQubit as cirq_NamedQubit
from cirq.ops.qubit_order import QubitOrder as cirq_QubitOrder
from cirq.ops.gate_features import SingleQubitGate as cirq_SingleQubitGate
from cirq.ops.gate_features import TwoQubitGate as cirq_TwoQubitGate
from cirq.ops.gate_features import ThreeQubitGate as cirq_ThreeQubitGate
from cirq.ops.gate_operation import GateOperation as cirq_GateInstruction
from cirq.ops.moment import Moment as cirq_Moment
from cirq.circuits import Circuit as cirq_Circuit


def to_aws(any_quantum_object):
    aqo = copy.copy(any_quantum_object)
    t = type(aqo)
    
    if t == aws_Qubit or t == aws_QubitSet or t == aws_Gate or t == aws_Instruction or t == aws_Moments or t == aws_Circuit:
        return aqo
        
    if t == cirq_NamedQubit: # or t == [other_package]_Qubit or ...
        qb_qubit = qB_Qubit(aqo).to_qB()
        return aws_Qubit(qb_qubit.name)
    
    if t == cirq_QubitOrder: # or t == [other_package]_QubitSet or ...
        qb_qubitset = qB_QubitSet(aqo)
        qb_qubitset = qb_qubitset.to_qB()
        return aws_QubitSet([qubit.name for qubit in qb_qubitset.qubits])
    
    if t == cirq_SingleQubitGate or t == cirq_TwoQubitGate or t == cirq_ThreeQubitGate: # or t == [other_package]_Gate or ...
        qb_gate = qB_Gate(aqo).to_qB()
        return qb_gate
        """ TODO: Implement getting aws_Gate from qB_Gate """
        #return aws_Gate()
    
    if t == cirq_GateInstruction: # or t == [other_package]_Instruction
        qb_instruction = qB_Instruction(aqo).to_qB()
        return qb_instruction
    """ TODO: Implement getting aws_Instruction from qB_Instruction """
        #return aws_Instruction()
        
    if t == cirq_Moment: # or t == [other_package]_Moment
        qb_moment = qB_Moment(aqo).to_qB()
        return qb_moment
    """ TODO: Implement getting aws_Moments from qB_Moment """
        #return aws_Moments()
        
    if t == cirq_Circuit: # or t == [other_package]_Circuit
        qb_circuit = qB_Circuit(aqo).to_qB()
        return qb_circuit
    """ TODO: Implement getting aws_Circuit from qB_Circuit """
        #return aws_Circuit()
        
        
        
        
        
def to_cirq(any_quantum_object):
    aqo = copy.copy(any_quantum_object)
    t = type(aqo)
    
    if t == cirq_NamedQubit or t == cirq_QubitOrder: # or t == cirq_SingleQubitGate or t == cirq_TwoQubitGate or t == cirq_ThreeQubitGate or t == cirq_Instruction or t == cirq_Moment or t == cirq_Circuit:
        return aqo
        
    if t == aws_Qubit: # or t == [other_package]_Qubit or ...
        qb_qubit = qB_Qubit(aqo).to_qB()
        return cirq_NamedQubit(str(qb_qubit.name))
    
    if t == aws_QubitSet: # or t == [other_package]_QubitSet or ...
        qb_qubitset = qB_QubitSet(aqo).to_qB()
        return cirq_QubitOrder([qubit.name for qubit in qb_qubitset.qubits])
    
    # ...
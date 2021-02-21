from typing import Any, Sequence, Dict, Iterable, Union
import numpy as np


from gate import Gate
from qubitset import QubitSet
from clbitset import ClbitSet

from braket.circuits.instruction import Instruction as BraketInstruction
from qiskit.circuit import Instruction as QiskitInstruction
from qiskit.circuit.gate import Gate as QiskitGate
from cirq.ops.gate_operation import GateOperation as CirqGateInstruction

InstructionInput = Union["BraketInstruction", 
                            "CirqGateInstruction",
                            "QiskitInstruction", 
                            Gate, 
                            np.array]

class Instruction():
    
    """
    qBraid Instruction class
    
    Arguments:
        instruction:
    
    Attributes:
        gate: action to perform on qubits
        target: qubit(s) to perform operation on
        _holding: ____
        
    Methods:
        
         
    """
    
    def __init__(self, instruction: InstructionInput = None, qubits: QubitSet = None, clbits: ClbitSet =None):
        
        self.instruction = instruction
        self.qubits = qubits
        self.clbits = clbits
        
        if isinstance(instruction,BraketInstruction):
            pass
        
        elif isinstance(instruction,QiskitInstruction):
            self.gate = Gate(instruction)    
            
        elif isinstance(instruction,CirqGateInstruction):
            #instruction is a cirq operation object
            self.gate = Gate(instruction.gate)
        
    def to_cirq(self):
        
        #print(self.qubits)
        qubits = [qubit.to_cirq() for qubit in self.qubits]
        gate = self.gate.to_cirq()
        
        return gate(*qubits)
        
    def to_qiskit(self):
        
        gate = self.gate.to_qiskit()
        qubits = [qubit.to_qiskit() for qubit in self.qubits]
        clbits = []
        
        return gate,qubits,clbits
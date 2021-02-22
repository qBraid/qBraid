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
                         "QiskitInstruction"]

class Instruction():
    
    """
    qBraid Instruction class
    
    Arguments:
        instruction:
    
    Attributes:
        
    Methods:
        
         
    """
    
    def __init__(self, instruction: InstructionInput = None, qubits: QubitSet = None, clbits: ClbitSet =None):
        
        self.instruction = instruction
        self.qubits = qubits
        self.clbits = clbits
        
        if isinstance(instruction,BraketInstruction):
            self.gate = Gate(instruction.operator)
        
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
    
    def to_braket(self):
        
        gate = self.gate.to_braket()
        qubits = [qubit.to_braket() for qubit in self.qubits]
        clbits = []
        
        return BraketInstruction(gate,qubits)
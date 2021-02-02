from typing import Any, Sequence, Dict, Iterable, Union
import numpy as np

##################################

from circuits.gate import qB_Gate
from circuits.qubitset import qB_QubitSet

from braket.circuits.instruction import Instruction as aws_Instruction
from qiskit.circuit import Instruction as qiskit_Instruction
from cirq.ops.gate_operation import GateOperation as cirq_GateInstruction

##################################

qB_InstructionInput = Union["aws_Instruction", 
                            "cirq_GateInstruction",
                            "qiskit_Instruction", 
                            qB_Gate, 
                            np.array]

class qB_Instruction():
    
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
    
    def __init__(self, instruction: qB_InstructionInput = None, qubits: qB_QubitSet = None):
        
        self._holding = True
        if type(instruction) == np.array:
            self._holding = False
            instruction = qB_Gate(instruction)
            
        if type(instruction) == qB_Gate:
            self._holding = False
    
            if qubits == None:
                print("Error: please pass target qubits to define new instruction from gate")
                raise # TODO: implement exception
                
            if instruction.num_qubits != len(qubits):
                print("Error: incorrect number of target qubits for gate: " + instruction.name)
                raise # TODO: implement exception
                
            self.gate = instruction
            self.target = qubits
            
            self._instruction = self
            
        if self._holding:
            self._instruction = instruction
            
    def __str__(self):
        if self._holding:
            return str(self._instruction)
        return str(self.gate) + ': ' + str(self.target)
        
from ..instruction import AbstractInstructionWrapper
from .gate import BraketGateWrapper

from braket.circuits.instruction import Instruction as BraketInstruction

class BraketInstructionWrapper(AbstractInstructionWrapper):
    
    def __init__(self, instruction: BraketInstruction,
                 qubits,
                 clbits = None):
        
        super().__init__()
        
        self.instruction = instruction
        self.qubits = qubits
        self.clbits = clbits
        self.package = 'braket'
        self.gate = BraketGateWrapper(instruction.operator)
        

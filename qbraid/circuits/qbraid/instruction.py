from ..instruction import AbstractInstructionWrapper
from .gate import QbraidGateWrapper

class QbraidInstructionWrapper(AbstractInstructionWrapper):
    
    def __init__(self, qbraid_gate: QbraidGateWrapper,
                 qubits,
                 clbits = None):
        
        super().__init__()
        
        self.instruction = qbraid_gate
        self.qubits = qubits
        self.clbits = clbits
        self.package = 'qbraid'
        
        """
        self.instruction = instruction
        self.qubits = qubits
        self.clbits = clbits
        self.package = 'braket'
        self.gate = Gate(instruction.operator)
        """


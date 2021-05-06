from ..instruction import AbstractInstructionWrapper
from .gate import QiskitGateWrapper

from qiskit.circuit import Instruction as QiskitInstruction
from qiskit.circuit.gate import Gate as QiskitGate

class QiskitInstructionWrapper(AbstractInstructionWrapper):
    
    def __init__(self, instruction: QiskitInstruction,
                 qubits,
                 clbits = None,
                 params = None):
        
        super().__init__()
        
        self.instruction = instruction
        self.qubits = qubits
        self.clbits = clbits
        self.package = 'qiskit'
        
        self.gate = QiskitGateWrapper(instruction, params)
    
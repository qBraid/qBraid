from ..instruction import InstructionWrapper
from .gate import BraketGateWrapper

from braket.circuits.instruction import Instruction as BraketInstruction


class BraketInstructionWrapper(InstructionWrapper):
    def __init__(self, instruction: BraketInstruction, qubits):
        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.gate = BraketGateWrapper(instruction.operator)

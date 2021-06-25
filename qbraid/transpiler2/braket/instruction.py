from ..instruction import AbstractInstructionWrapper
from .gate import BraketGateWrapper

from braket.circuits.instruction import Instruction as BraketInstruction


class BraketInstructionWrapper(AbstractInstructionWrapper):
    def __init__(self, instruction: BraketInstruction, qubits):

        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.gate = BraketGateWrapper(instruction.operator)

    @property
    def package(self):
        return 'braket'
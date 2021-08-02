from qbraid.circuits.instruction import Instruction as QbraidInstruction
from .gate import QbraidGateWrapper
from ..instruction import InstructionWrapper
# from qbraid.circuits.parameter import Parameter


class QbraidInstructionWrapper(InstructionWrapper):

    def __init__(self, instruction: QbraidInstruction):
        super().__init__()

        self.gate = QbraidGateWrapper(instruction.gate)
        self.qubits = instruction.qubits

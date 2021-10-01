"""QbraidInstructionWrapper Class"""

from qbraid.circuits.instruction import Instruction as QbraidInstruction
from qbraid.transpiler.instruction import InstructionWrapper
from qbraid.transpiler.qbraid.gate import QbraidGateWrapper

# from qbraid.circuits.parameter import Parameter


class QbraidInstructionWrapper(InstructionWrapper):
    """Wrapper class for qBraid ``Instruction`` objects."""

    def __init__(self, instruction: QbraidInstruction):
        """Create a QbraidInstructionWrapper

        Args:
            instruction: the qbraid ``Instruction`` object to be wrapped

        """
        super().__init__()

        self.gate = QbraidGateWrapper(instruction.gate)
        self.qubits = instruction.qubits

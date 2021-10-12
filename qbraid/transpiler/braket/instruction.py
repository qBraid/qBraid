"""BraketInstructionWrapper Class"""

from braket.circuits.instruction import Instruction as BraketInstruction

from qbraid.transpiler.braket.gate import BraketGateWrapper
from qbraid.transpiler.instruction import InstructionWrapper


class BraketInstructionWrapper(InstructionWrapper):
    """Wrapper class for Amazon Braket ``Instruction`` objects."""

    def __init__(self, instruction: BraketInstruction, qubits):
        """Create a BraketInstructionWrapper

        Args:
            instruction: the Braket ``Instruction`` to be wrapped
            qubits: list of the qubits to which the instruction applies

        """
        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.gate = BraketGateWrapper(instruction.operator)
        self.package = "braket"

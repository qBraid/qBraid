"""QiskitInstructionWrapper Class"""

from qiskit.circuit import Instruction

from qbraid.transpiler.instruction import InstructionWrapper
from qbraid.transpiler.qiskit.gate import QiskitGateWrapper


class QiskitInstructionWrapper(InstructionWrapper):
    """Wrapper class for Qiskit ``Instruction`` objects"""

    def __init__(self, instruction: Instruction, qubits, params=None):
        """Create a QiskitInstructionWrapper

        Args:
            instruction: the qiskit ``Instruction`` object to be wrapped
            qubits: list of the qubits associated with the instruction
            params: list of the paramaters associated with the instruction

        """
        super().__init__()

        if params is None:
            params = []
        self.instruction = instruction
        self.qubits = qubits

        self.gate = QiskitGateWrapper(instruction, params)
        self._params = params
        self.package = "qiskit"

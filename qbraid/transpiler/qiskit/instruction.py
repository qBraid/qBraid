from qiskit.circuit import Instruction

from ..instruction import InstructionWrapper
from .gate import QiskitGateWrapper


class QiskitInstructionWrapper(InstructionWrapper):
    def __init__(self, instruction: Instruction, qubits, params=None):
        super().__init__()

        if params is None:
            params = []
        self.instruction = instruction
        self.qubits = qubits

        self.gate = QiskitGateWrapper(instruction, params)
        self._params = params

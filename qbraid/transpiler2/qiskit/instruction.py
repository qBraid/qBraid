from ..instruction import AbstractInstructionWrapper
from .gate import QiskitGateWrapper

from qiskit.circuit import Instruction
from qiskit.circuit.gate import Gate


class QiskitInstructionWrapper(AbstractInstructionWrapper):
    def __init__(self, instruction: Instruction, qubits, params=None):

        super().__init__()

        self.instruction = instruction
        self.qubits = qubits

        self.gate = QiskitGateWrapper(instruction, params)
        self.params = self.gate.get_abstract_params()

    @property
    def package(self):
        return 'qiskit'
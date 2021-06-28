from ..instruction import InstructionWrapper
from .gate import QiskitGateWrapper

from qiskit.circuit import Instruction
from qiskit.circuit.gate import Gate


class QiskitInstructionWrapper(InstructionWrapper):
    def __init__(self, instruction: Instruction, qubits, params=[]):

        super().__init__()

        self.instruction = instruction
        self.qubits = qubits

        self.gate = QiskitGateWrapper(instruction, params)
        self.params = params

    @property
    def package(self):
        return 'qiskit'
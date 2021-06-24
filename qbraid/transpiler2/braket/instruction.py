from ..instruction import AbstractInstructionWrapper
from .gate import BraketGateWrapper

from braket.circuits.instruction import Instruction as BraketInstruction


class BraketInstructionWrapper(AbstractInstructionWrapper):
    def __init__(self, instruction: BraketInstruction, qubits):

        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.package = "braket"
        self.gate = BraketGateWrapper(instruction.operator)

    def transpile(self, package: str, output_mapping: dict = None):        

        if package == "braket":
            from ..braket.outputs import instruction_to_braket
            return instruction_to_braket(self, output_mapping)
        elif package == "cirq":
            from ..cirq.outputs import instruction_to_cirq
            return instruction_to_cirq(self, output_mapping)
        elif package == "qiskit":
            from ..qiskit.outputs import instruction_to_qiskit
            return instruction_to_qiskit(self, output_mapping)
        else:
            raise TypeError #PackageError(package)
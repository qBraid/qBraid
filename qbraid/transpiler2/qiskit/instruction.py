from ..instruction import AbstractInstructionWrapper
from .gate import QiskitGateWrapper

from qiskit.circuit import Instruction
from qiskit.circuit.gate import Gate


class QiskitInstructionWrapper(AbstractInstructionWrapper):
    def __init__(self, instruction: Instruction, qubits, clbits=None, params=None):

        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.clbits = clbits
        self.package = "qiskit"

        self.gate = QiskitGateWrapper(instruction, params)

    def transpile(self, package: str, output_mapping: dict = None):        

        if package == "braket":
            from ..braket.outputs import instruction_to_braket
            return instruction_to_braket(self, output_mapping)
        elif package == "cirq":
            from ..cirq.outputs import instruction_to_cirq
            return instruction_to_cirq(self, output_mapping)
        elif package == "qiskit":
            raise NotImplementedError
        else:
            raise TypeError #PackageError(package)
from ..instruction import AbstractInstructionWrapper
from .gate import CirqGateWrapper
from cirq.ops.gate_operation import GateOperation as CirqInstruction

class CirqInstructionWrapper(AbstractInstructionWrapper):
    def __init__(self, instruction: CirqInstruction, qubits, clbits=None):

        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.package = "cirq"
        self.gate = CirqGateWrapper(instruction.gate)

    def transpile(self, package: str, output_mapping: dict):        

        if package == "braket":
            from ..braket.outputs import instruction_to_braket
            return instruction_to_braket(self, output_mapping)
        elif package == "cirq":
            raise NotImplementedError #should be implemented
        elif package == "qiskit":
            from ..qiskit.outputs import instruction_to_qiskit
            return instruction_to_qiskit(self, output_mapping)
        else:
            raise TypeError #PackageError(package)
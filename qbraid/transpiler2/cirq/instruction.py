from ..instruction import InstructionWrapper
from .gate import CirqGateWrapper
from cirq.ops.gate_operation import GateOperation as CirqInstruction


class CirqInstructionWrapper(InstructionWrapper):
    def __init__(self, instruction: CirqInstruction, qubits):

        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.gate = CirqGateWrapper(instruction.gate)
        self.params = self.gate.get_abstract_params()

    @property
    def package(self):
        return "cirq"

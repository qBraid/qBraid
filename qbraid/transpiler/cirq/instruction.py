from ..instruction import AbstractInstructionWrapper
from .gate import CirqGateWrapper
from cirq.ops.gate_operation import GateOperation as CirqInstruction


class CirqInstructionWrapper(AbstractInstructionWrapper):
    def __init__(self, instruction: CirqInstruction, qubits, clbits=None):

        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.clbits = clbits
        self.package = "cirq"
        self.gate = CirqGateWrapper(instruction.gate)

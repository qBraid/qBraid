from ..instruction import InstructionWrapper
from ..parameter import ParamID
from .gate import CirqGateWrapper
from cirq.ops.raw_types import Operation as CirqInstruction

# from cirq.ops.gate_operation import GateOperation as CirqInstruction


class CirqInstructionWrapper(InstructionWrapper):
    def __init__(self, instruction: CirqInstruction, qubits):
        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.gate = CirqGateWrapper(instruction.gate)

    @property
    def params(self):
        return [p for p in self.gate.params if isinstance(p, ParamID)]

    @property
    def package(self):
        return "cirq"

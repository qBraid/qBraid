from cirq.ops.raw_types import Operation as CirqInstruction
# from cirq.ops.gate_operation import GateOperation as CirqInstruction

from qbraid.transpiler.instruction import InstructionWrapper
from qbraid.transpiler.parameter import ParamID
from .gate import CirqGateWrapper


class CirqInstructionWrapper(InstructionWrapper):
    def __init__(self, instruction: CirqInstruction, qubits):
        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.gate = CirqGateWrapper(instruction.gate)

    @property
    def params(self):
        return [p for p in self.gate.params if isinstance(p, ParamID)]

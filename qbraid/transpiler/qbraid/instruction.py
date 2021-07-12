from ..instruction import InstructionWrapper
from .gate import QbraidGateWrapper


class QbraidInstructionWrapper(InstructionWrapper):
    def __init__(self, qbraid_gate: QbraidGateWrapper, qubits, clbits=None):

        super().__init__()

        self.instruction = qbraid_gate
        self.qubits = qubits
        self.clbits = clbits
        self._package = "qbraid"
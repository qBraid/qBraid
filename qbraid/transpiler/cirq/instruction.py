"""CirqInstructionWrapper Class"""

from cirq.ops.raw_types import Operation as CirqInstruction

from qbraid.transpiler.instruction import InstructionWrapper
from qbraid.transpiler.parameter import ParamID
from qbraid.transpiler.cirq.gate import CirqGateWrapper


class CirqInstructionWrapper(InstructionWrapper):
    """Wrapper class for Cirq ``Operation`` objects."""

    def __init__(self, instruction: CirqInstruction, qubits):
        """Create a CirqInstructionWrapper

        Args:
            instruction: the cirq ``Operation`` to be wrapped.
            qubits: list of the qubits to which the instruction applies

        """
        super().__init__()

        self.instruction = instruction
        self.qubits = qubits
        self.gate = CirqGateWrapper(instruction.gate)

    @property
    def params(self):
        """Return the paramaters associated with the instruction."""
        return [p for p in self.gate.params if isinstance(p, ParamID)]

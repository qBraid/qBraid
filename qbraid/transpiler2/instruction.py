from abc import ABC
from braket.circuits.instruction import Instruction as BraketInstruction

from qbraid.exceptions import PackageError


class AbstractInstructionWrapper(ABC):
    def __init__(self):

        self.instruction = None
        self.qubits = []

        self.package = None
        self.gate = None
        self.params = None

        self._outputs = {}

    def transpiile(self):
        
        raise NotImplementedError

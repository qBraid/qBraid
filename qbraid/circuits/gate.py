from abc import ABC, abstractmethod
from typing import Optional, List


class Gate(ABC):
    """Abstract class for gate library to extend and apply to instructions.

    Args:
        ABC (ABC): Extends Abstract Class

    Returns:
        None: No return for abstract class
    """

    @abstractmethod
    def __init__(
        self,
        name: str,
        num_qubits: int,
        params: List = None,
        global_phase: Optional[float] = 0.0,
    ):
        self._name = name
        self._num_qubits = num_qubits
        self._params = [] if params is None else params
        self._global_phase = global_phase

    @property
    def name(self):
        return self._name

    @property
    def num_qubits(self):
        return self._num_qubits

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, params: List):
        self._params = params

    @property
    def global_phase(self):
        return self._global_phase if hasattr(self, "_global_phase") else 0.0

    @global_phase.setter
    def global_phase(self, value: Optional[float] = 0.0):
        self._global_phase = value

    def on(self, qubits):
        # avoid circular import
        from qbraid.circuits.instruction import Instruction

        return Instruction(self, qubits)

    def __call__(self, qubits):
        return self.on(qubits)

    def control(self, num_ctrls: Optional[int] = 1):

        from .controlledgate import ControlledGate

        return ControlledGate(self, num_ctrls, self)

from abc import ABC, abstractmethod
from typing import Optional, List

from qbraid.circuits.exceptions import CircuitError


class Gate(ABC):
    """Abstract class for gate library to extend and apply to instructions."""

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
        return self._params if hasattr(self,'_params') else []

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

    def _check_params(self, params, expected_num_params):
            
        if len(params) != expected_num_params:
            raise CircuitError(f'Expected {expected_num_params} params but received {len(params)}.')

        from .parameter import Parameter
        for p in params:
            if not isinstance(p,(Parameter,float,int)):
                raise CircuitError(f'Unexpected type {type(p)} for parameter input.')



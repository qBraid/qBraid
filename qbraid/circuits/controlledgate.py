from typing import Optional, List
from abc import abstractmethod

from .gate import Gate


class ControlledGate(Gate):
<<<<<<< HEAD
    """Extension of Gate for standard gates with a controlled operation

    Args:
        Gate (Gate(ABC)): Extensions of basic gate class
    """
=======
    def __init__(
        self,
        base_gate,
        num_ctrls: Optional[int] = 1,
        global_phase: Optional[float] = 0.0,
    ):
        self._global_phase = global_phase
        self._num_ctrls = num_ctrls
        self._base_gate = base_gate

    @property
    def num_qubits(self):
        return self.num_ctrls + self.base_gate.num_qubits
>>>>>>> 04ec590e17fa8a808f29650c735404918a2c4b99

    @property
    def num_ctrls(self):
        return self._num_ctrls

    @num_ctrls.setter
    def num_ctrls(self, value):
        self._num_ctrls = value

    @property
    def base_gate(self):
        return self._base_gate

    @base_gate.setter
    def base_gate(self, gate):
        self._base_gate = gate

    @property
    def name(self):
        if self._num_ctrls > 2:
            return f'C{self._num_ctrls}{self._base_gate.name}'
        else:
            c_s = 'C'*self._num_ctrls
            return c_s + self._base_gate.name
            

    def control(self, num_ctrls:int = 1):
        self._num_ctrls += num_ctrls


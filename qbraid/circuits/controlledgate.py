from typing import Optional, List
from abc import abstractmethod
from .gate import Gate

class ControlledGate(Gate):

    def __init__(self, name, num_qubits: int, params: List, global_phase: Optional[float]=0.0, 
    num_ctrls: Optional[int]=1, base_gate: Optional[Gate]=None):
        super().__init__(name, num_qubits, params, global_phase=global_phase)
        self._num_ctrls=num_ctrls
        self._base_gate=base_gate
    
    @property
    @abstractmethod
    def num_ctrls(self):
        pass

    @num_ctrls.setter
    @abstractmethod
    def num_ctrls(self, value):
        self._num_ctrls=value

    @property
    def base_gate(self):
        raise NotImplementedError

    @base_gate.setter
    def base_gate(self, value):
        raise NotImplementedError

    @property
    def name(self):
        if self._num_ctrls > 2:
            return f'C{self._num_ctrls}{self._base_gate.name}'
        else:
            c_s = 'C'*self._num_ctrls
            return c_s + self._base_gate.name

    def control(self, num_ctrls:int = 1):
        self._num_ctrls += num_ctrls
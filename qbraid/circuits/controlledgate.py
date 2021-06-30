from typing import Optional
from gate import Gate

class ControlledGate(Gate):

    @abc.abstractmethod
    def __init__(self, name: str, num_qubits: int, params: List, global_phase: Optional[float]=0.0, exponent: Optional[float]=1, 
    num_ctrls: Optional[int]=1, base_gate: Optional[Gate]=None):
        super().__init__(name, num_qubits, params, global_phase=global_phase, exponent=exponent)
        self._num_ctrls=num_ctrls
        self._base_gate=base_gate
    
    @property
    @abc.abstractmethod
    def num_ctrls(self):
        pass

    @num_ctrls.setter
    @abc.abstractmethod
    def num_ctrls(self, value):
        self._num_ctrls=value

    @property
    @abc.abstractmethod
    def base_gate(self):
        pass

    @base_gate.setter
    @abc.abstractmethod
    def base_gate(self, value):
        pass
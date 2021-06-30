from abc import ABC
from typing import Optional, List
from gate import ControlledGate

class Gate(ABC):

    @abc.abstractmethod
    def __init__(self, name: str, num_qubits: int, params: List, global_phase: Optional[float]=0.0, exponent: Optional[float]=1):
        self._name=name
        self._num_qubits=num_qubits
        self._params=params
        self._global_phase=global_phase
        self._exponent=exponent
    
    @property
    @abc.abstractmethod
    def name(self):
        pass

    @property
    @abc.abstractmethod
    def num_qubits(self):
        pass

    @property
    @abc.abstractmethod
    def params(self):
        pass

    @params.setter
    @abc.abstractmethod
    def params(self, value: List):
        pass

    @property
    @abc.abstractmethod
    def global_phase(self):
        pass

    @global_phase.setter
    @abc.abstractmethod
    def global_phase(self, value: Optional[float]=0.0):
        pass

    @property
    @abc.abstractmethod
    def exponent(self):
        pass

    @exponent.setter
    @abc.abstractmethod
    def exponent(self, value):
        pass

    def on(self, qubits):
        
        #avoid circular import
        from qbraid.circuits.instruction import Instruction
        return Instruction(self,qubits)
    
    def __call__(self, qubits):
        return self.on(qubits)

    def control(self, num_ctrls: Optional[int]=1):
        
        if self._num_ctrls==0:
            return ControlledGate("CUnitary", self._num_qubits+1, self._params, self._global_phase, self._exponent, num_ctrls)
        else:
            self._num_ctrls+=num_ctrls
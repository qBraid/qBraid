from abc import ABC
from typing import Optional

class Gate(ABC):
    
    @property
    @abc.abstractmethod
    def name(self):
        pass

    def on(self, qubits):
        
        #avoid circular import
        from qbraid.circuits.instruction import Instruction
        return Instruction(self,qubits)
    
    def __call__(self, qubits):
        return self.on(qubits)

    def control(self, num_ctrls: Optional[int]=1):
        pass  
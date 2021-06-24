from abc import ABC

#from .utils import create_instruction

class Gate(ABC):
    
    def __init__(self):
        
        raise NotImplementedError
        
    
    def __call__(self, qubits):
        
        return create_instruction(self,qubits)
from abc import ABC

class Gate(ABC):
    
    def on(self, qubits):
        
        #avoid circular import
        from qbraid.circuits.instruction import Instruction
        return Instruction(self,qubits)
    
    def __call__(self, qubits):
        return self.on(qubits)
    
class TestGate(Gate):
    
    def __init__(self):
        self.name = 'Test'
        
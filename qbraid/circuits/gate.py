from abc import ABC

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


class ControlledGate(Gate):
    pass


        
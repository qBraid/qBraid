from typing import Type, Union, Iterable

from .gate import Gate

class Instruction:
    
    def __init__(self, gate: Gate, qubits: Union[int,Iterable[int]]):
        
        self._gate = gate

        if isinstance(qubits, int):
            self._qubits = [qubits]
        elif isinstance(qubits, Iterable):
            if len(qubits) == gate.num_qubits:
                print(gate.num_qubits)
                self._qubits = qubits
            else:
                raise AttributeError(f"The input {qubits} is the incorrect number of qubits for .")
        else:
            raise AttributeError(f"The input type {type(qubits)} is invalid.")
        
        
    @property
    def gate(self):
        return self._gate
    
    @property
    def qubits(self):
        return self._qubits
    
    def __str__(self) -> str:
        return f'Instruction ({self._qubits} qubits, {self._gate} gate)'
    
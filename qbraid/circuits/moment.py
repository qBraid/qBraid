from typing import Union, Iterable

from .instruction import Instruction
from .qubit import Qubit

class Moment:
    
    def __init__(self, instructions: Union[Instruction, Iterable[Instruction]] = []):
        
        self._instructions = instructions
    
    @property
    def qubits(self) -> Iterable[Qubit]:
        
        out = set()
        for instruction in self._instructions:
            out.add(instruction.qubits)
        return list[out]
    
    
    def append(self, instruction: Union[Instruction, Iterable[Instruction]]) -> None:
        
        #TO DO validate args from user
        
        if isinstance(instruction, Iterable):
            for i in instruction:
                self._append(i)
            else:
                self._append(instruction)
   
    def _append(self, instruction: Instruction) -> None:
       
       self._instructions.append(instruction)
   
    @property
    def instructions(self):
        return self._instructions

            
    
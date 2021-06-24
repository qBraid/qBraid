from typing import Iterable

from .instruction import Instruction
from .gate import Gate

def create_instruction(gate: Gate, qubits: Iterable[int]) -> Instruction:
    
    return Instruction(gate,qubits)
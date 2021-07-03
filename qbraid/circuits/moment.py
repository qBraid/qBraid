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

    def appendable(self, instruction):
        return set(instruction.qubits).isdisjoint(self.qubits)

    def append(self, instruction: Union[Instruction, Iterable[Instruction]]) -> None:

        # TO DO validate args from user

        if isinstance(instruction, Iterable):
            for i in instruction:
                self.append(i)
            else:
                self._append(i)

    def _append(self, instruction: Instruction) -> None:

        if self.appendable(instruction):
            self._instructions.append(instruction)
        else:
            raise TypeError  # should be CircuitError

    @property
    def instructions(self):
        return self._instructions

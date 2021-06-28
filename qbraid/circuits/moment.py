import logging
from typing import Type, Union, Iterable

from .exceptions import CircuitError
from .instruction import Instruction
from .qubit import Qubit

log = logging.getLogger(__name__)


class Moment:
    def __init__(self, instructions: Union[Instruction, Iterable[Instruction]] = None):
        if instructions is None:
            self._instructions = []
        else:
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
        """
        Appends instructions onto the end of the moment.
        Args:
            instruction: The instruction or iterable of instructions to append.
        """
        # TODO: add generator appending functionality.
        if isinstance(instruction, Instruction):
            self._append(instruction)
        elif isinstance(instruction, Iterable):
            for i in instruction:
                self.append(i)
        # error
        else:
            raise TypeError(
                "Instructions of type {} not appendable".format(type(instruction))
            )

    def _append(self, instruction: Instruction) -> None:

        if self.appendable(instruction):
            self._instructions.append(instruction)
        else:
            raise CircuitError(
                "Instructions of type {} not appendable".format(type(instruction))
            )

    @property
    def instructions(self):
        return self._instructions

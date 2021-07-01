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
    def instructions(self):
        return self._instructions

    @property
    def qubits(self) -> Iterable[Qubit]:
        out = set()
        for instruction in self._instructions:
            out.add(instruction.qubits)
        return [out]

    def __repr__(self):
        return f'Moment("{self.instructions}")'

    def appendable(self, instruction):
        return set(instruction.qubits).isdisjoint(self.qubits)

    def append(self, instruction: Union[Instruction, Iterable[Instruction]]) -> None:
        """
        Wrapper which preps instructions to be appended, throws error if not appendable.
        Args:
            instruction: The instruction or iterable of instructions to append.
        """
        # TODO: add generator appending functionality.
        if isinstance(instruction, Instruction):
            self._insert(instruction)
        # might be redundant to have iterable here since circuit only appends Instructions or Moments.
        elif isinstance(instruction, Iterable):
            for i in instruction:
                self.append(i)
        # error
        else:
            raise TypeError(
                "Instructions of type {} not appendable".format(type(instruction))
            )

    def _insert(self, instruction: Instruction) -> None:
        """
        Appends instructions onto the end of the moment
        Args:
            instruction (Instruction): Operations that are applied to qubit(s) in a circuit.

        Raises:
            CircuitError:  Errors that occur when constructing circuits with the qBraid circuit layer.
        """
        if self.appendable(instruction):
            self._instructions.append(instruction)
        else:
            raise CircuitError(
                "Instructions of type {} not appendable".format(type(instruction))
            )
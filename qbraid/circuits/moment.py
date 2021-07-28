# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Set, Union, Iterable

from .exceptions import CircuitError
from .instruction import Instruction
from .qubit import Qubit

log = logging.getLogger(__name__)


class Moment:
    """
    A time-slice of instructions within a circuit.
    Grouping instructions into moments is intended to be a strong suggestion to
    whatever is scheduling instructions on real hardware. instructions in the same
    moment should execute at the same time (to the extent possible; not all
    instructions have the same duration) and it is expected that all instructions
    in a moment should be completed before beginning the next moment.
    Moment can be indexed by qubit or list of qubits:
    """

    def __init__(self, instructions: Union[Instruction, Iterable[Instruction]] = None):
        if instructions is None:
            self._instructions = []
        elif isinstance(instructions, Iterable):
            self._instructions = instructions
        else:
            self._instructions = [instructions]

    @property
    def instructions(self):
        return self._instructions

    @property
    def qubits(self) -> Iterable[Qubit]:
        out = set()
        for instruction in self._instructions:
            out.update(instruction.qubits)
        return list(out)

    def __repr__(self):
        return f'Moment("{self.instructions}")'

    def appendable(self, instruction: Instruction) -> bool:
        """Checks that the instructions are disjoint from the qubits acted on in the moment.

        Args:
            instruction (Instruction): Instruction that needs to be checked.

        Returns:
            bool: True if disjoint, false otherwise.
        """
        return set(instruction.qubits).isdisjoint(self.qubits)

    def append(self, instruction: Union[Instruction, Iterable[Instruction], Set]) -> None:

        """Wrapper which preps instructions to be appended, throws error if not appendable.

        Args:
            instruction (Union[Instruction, Iterable[Instruction], Set]):
            The instruction or iterable of instructions to append.

        Raises:
            TypeError: Non appendable type.
        """
        # TODO: add generator appending functionality.
        if isinstance(instruction, Instruction):
            self._insert(instruction)
        # might be redundant to have iterable here since circuit
        # only appends Instructions or Moments.
        elif isinstance(instruction, Iterable):
            for i in instruction:
                self.append(i)
        # error
        else:
            raise TypeError("Instructions of type {} not appendable".format(type(instruction)))

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
            raise CircuitError("Instructions of type {} not appendable".format(type(instruction)))

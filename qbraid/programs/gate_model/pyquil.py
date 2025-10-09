# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module defining PyQuilProgram Class

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pyquil import Program
from pyquil.quilbase import Declare, Measurement
from pyquil.simulation.tools import program_unitary

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram

if TYPE_CHECKING:
    import numpy as np
    import pyquil


class PyQuilProgram(GateModelProgram):
    """Wrapper class for ``pyQuil.Program`` objects."""

    def __init__(self, program: pyquil.Program):
        super().__init__(program)
        if not isinstance(program, Program):
            raise ProgramTypeError(
                message=f"Expected 'pyquil.Program' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[int]:
        """Return the qubits acted upon by the operations in this circuit"""
        return list(self.program.get_qubits())

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return 0

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        return len(self.program)

    @staticmethod
    def remove_measurements(original_program):
        """Remove MEASURE and DECLARE instructions from a pyQuil program."""
        program = Program()
        for instruction in original_program:
            if not isinstance(instruction, Measurement) and not isinstance(instruction, Declare):
                program += instruction
        return program

    def _unitary(self) -> np.ndarray:
        """Return the unitary of a pyQuil program."""
        program_copy = self.remove_measurements(self.program)
        return program_unitary(program_copy, n_qubits=self.num_qubits)

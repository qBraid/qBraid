# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

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

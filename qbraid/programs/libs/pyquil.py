# Copyright (C) 2023 qBraid
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

from typing import List

import numpy as np
import pyquil
from pyquil import Program
from pyquil.quilbase import Declare, Measurement
from pyquil.simulation.tools import program_unitary

from qbraid.programs.abc_program import QuantumProgram


class PyQuilProgram(QuantumProgram):
    """Wrapper class for ``pyQuil.Program`` objects."""

    def __init__(self, program: "pyquil.Program"):
        super().__init__(program)

    @property
    def program(self) -> pyquil.Program:
        return self._program

    @program.setter
    def program(self, value: pyquil.Program) -> None:
        if not isinstance(value, pyquil.Program):
            raise ValueError("Program must be an instance of pyquil.Program")
        self._program = value

    @property
    def qubits(self) -> List[int]:
        """Return the qubits acted upon by the operations in this circuit"""
        return list(self.program.get_qubits())

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return len(self.qubits)

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

    def _unitary(self) -> "np.ndarray":
        """Return the unitary of a pyQuil program."""
        program_copy = self.remove_measurements(self.program)
        return program_unitary(program_copy, n_qubits=self.num_qubits)

    def remove_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        raise NotImplementedError

    def reverse_qubit_order(self) -> None:
        """Reverse the order of the qubits in the circuit."""
        raise NotImplementedError

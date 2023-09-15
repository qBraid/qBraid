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
from pyquil.simulation.tools import program_unitary

from qbraid.programs.abc_program import QuantumProgram


class PyQuilProgram(QuantumProgram):
    """Wrapper class for ``pyQuil.Program`` objects."""

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

    def _unitary(self) -> "np.ndarray":
        """Return the unitary of a pyQuil program."""
        return program_unitary(self.program, n_qubits=self.num_qubits)

    def _contiguous_expansion(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, adds identity gates to vacant registers as needed."""
        raise NotImplementedError

    def _contiguous_compression(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        raise NotImplementedError

    def reverse_qubit_order(self) -> None:
        """Reverse the order of the qubits in the circuit."""
        raise NotImplementedError

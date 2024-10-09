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
Module defining IonQProgram Class

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import IonQDict

from ._model import GateModelProgram

if TYPE_CHECKING:
    import numpy as np


class IonQProgram(GateModelProgram):
    """Wrapper class for ``IonQDict`` objects."""

    def __init__(self, program: IonQDict):
        super().__init__(program)
        if not isinstance(program, IonQDict):
            raise ProgramTypeError(message=f"Expected 'IonQDict' object, got '{type(program)}'.")

    @property
    def qubits(self) -> list[int]:
        """Return the qubits acted upon by the operations in this circuit"""
        num_qubits: int = self.program["qubits"]
        return list(range(num_qubits))

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return 0

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        raise NotImplementedError

    def _unitary(self) -> np.ndarray:
        """Return the unitary of a pyQuil program."""
        raise NotImplementedError

    def remove_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        raise NotImplementedError

    def reverse_qubit_order(self) -> None:
        """Reverse the order of the qubits in the circuit."""
        raise NotImplementedError

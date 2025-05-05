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
Module defining CudaQKernel Class

"""
from __future__ import annotations

import base64

import cudaq

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram


class CudaQKernel(GateModelProgram):
    """Wrapper class for ``cudaq.PyKernel`` objects."""

    def __init__(self, program: cudaq.PyKernel):
        super().__init__(program)
        if not isinstance(program, cudaq.PyKernel):
            raise ProgramTypeError(
                message=f"Expected 'cudaq.PyKernel' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[int]:
        """Return the qubits acted upon by the operations in this circuit"""
        return list(range(self.num_qubits))

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        state = cudaq.get_state(self.program)
        return state.num_qubits()

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return 0

    def serialize(self) -> dict[str, str]:
        """Return the program in a format suitable for submission to the qBraid API."""
        qir: str = cudaq.translate(self.program, format="qir-base")
        return {"qir": base64.b64encode(qir.encode("utf-8")).decode("utf-8")}

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

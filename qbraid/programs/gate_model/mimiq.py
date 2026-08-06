# Copyright 2026 qBraid
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
Module defining MimiqProgram Class

"""
from __future__ import annotations

from mimiqcircuits import Circuit as MimiqCircuit

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram


class MimiqProgram(GateModelProgram):
    """Wrapper class for native ``mimiqcircuits`` ``Circuit`` programs.

    MIMIQ native circuits are submitted directly to the QPerfect cloud, so — like ``QiskitCircuit``
    and ``CirqCircuit`` — this class does not implement ``serialize`` (it inherits the base
    ``NotImplementedError``); it exists so the transpiler and ``QuantumDevice.validate`` can
    introspect a ``mimiq`` program (e.g. its qubit count).
    """

    def __init__(self, program: MimiqCircuit):
        super().__init__(program)
        if not isinstance(program, MimiqCircuit):
            raise ProgramTypeError(
                message=f"Expected a mimiqcircuits 'Circuit' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[int]:
        """Return the qubits acted upon by the operations in this circuit."""
        return list(range(self.program.num_qubits()))

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return self.program.num_bits()

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
Module defining IQMProgram class.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model._model import GateModelProgram

if TYPE_CHECKING:
    import iqm.iqm_client


class IQMProgram(GateModelProgram):
    """Wrapper class for ``iqm.iqm_client.Circuit`` objects.

    IQM circuits address qubits by name (``"QB1"``, or a logical name such as
    ``"q_0"`` that a device binds to a physical qubit at submission time), so
    :attr:`qubits` returns names rather than indices.
    """

    def __init__(self, program: iqm.iqm_client.Circuit):
        super().__init__(program)
        # pylint: disable-next=import-outside-toplevel
        from iqm.iqm_client import Circuit

        if not isinstance(program, Circuit):
            raise ProgramTypeError(
                message=f"Expected 'iqm.iqm_client.Circuit' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[str]:
        """Return the qubit names acted upon by the operations in this circuit."""
        seen: dict[str, None] = {}
        for instruction in self.program.instructions:
            for qubit in instruction.locus:
                seen.setdefault(qubit, None)
        return sorted(seen)

    @property
    def num_clbits(self) -> int:
        """Return the number of measured qubits, one classical bit each."""
        return sum(
            len(instruction.locus)
            for instruction in self.program.instructions
            if instruction.name == "measure"
        )

    def serialize(self) -> dict[str, str]:
        """Return the circuit as the JSON payload IQM's REST API accepts."""
        return {"iqmCircuit": self.program.model_dump_json()}

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
Module defining QrispCircuit Class

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import qrisp
from qrisp.circuit import Qubit
from qbraid.programs.exceptions import ProgramTypeError

from qbraid.programs.gate_model._model import GateModelProgram

if TYPE_CHECKING:
    import numpy as np


class QrispCircuit(GateModelProgram):
    """Wrapper class for ``qrisp.QuantumCircuit`` objects"""

    def __init__(self, program: qrisp.QuantumCircuit):
        super().__init__(program)
        if not isinstance(program, qrisp.QuantumCircuit):
            raise ProgramTypeError(
                message=f"Expected 'qrisp.QuantumCircuit' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[Qubit]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self.program.qubits

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return self.program.num_qubits()

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return len(self.program.clbits)

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        return self.program.depth()

    def _unitary(self) -> np.ndarray:
        """Calculate unitary of circuit. Removes measurement gates to
        perform calculation if necessary."""
        return self.program.get_unitary()

    def remove_idle_qubits(self) -> None:
        """Remove empty registers of circuit."""
        qubit_depths = self.program.get_depth_dic()
        idle_qubits = [q for q, d in qubit_depths.items() if d == 0]
        num_active_qubits = self.program.num_qubits() - len(idle_qubits)
        new_program = qrisp.QuantumCircuit(num_active_qubits, self.num_clbits)

        for instr in self.program.data:
            qubits = [self.program.qubits.index(q) for q in instr.qubits if q not in idle_qubits]
            clbits = [self.program.clbits.index(c) for c in instr.clbits]
            new_program.append(instr.op, qubits, clbits)

        self.program = new_program

    def reverse_qubit_order(self) -> None:
        """Rerverse qubit ordering of circuit."""
        self.program.qubits = [
            self.program.qubits[i] for i in reversed(range(self.program.num_qubits()))
        ]

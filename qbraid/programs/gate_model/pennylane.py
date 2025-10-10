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
Module defining PennylaneTape Class

"""
from typing import TYPE_CHECKING

import pennylane as qml
from pennylane.tape import QuantumTape

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram

if TYPE_CHECKING:
    import numpy as np


class PennylaneTape(GateModelProgram):
    """Wrapper class for Pennylane Quantum Tape programs."""

    def __init__(self, program: QuantumTape):
        super().__init__(program)
        if not isinstance(program, QuantumTape):
            raise ProgramTypeError(
                message=f"Expected 'pennylane.tape.QuantumTape' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[int]:
        """Returns the wires of the quantum tape as a list of ints"""
        return self.program.wires.tolist()

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the tape."""
        return 0

    @property
    def depth(self) -> int:
        """Calculates circuit depth of Pennylane tape"""
        tape = self.program

        op_count = {wire: 0 for wire in tape.wires}

        for op in tape.operations:
            for wire in op.wires:
                op_count[wire] += 1

        return max(op_count.values())

    def _unitary(self) -> "np.ndarray":
        """Return the unitary of the Pennylane tape"""
        return qml.matrix(self.program, wire_order=self.qubits)

    def remove_idle_qubits(self) -> None:
        """Applies a given wire map to all operations in a tape."""
        tape = self.program.copy()

        wires = sorted(tape.wires)
        contig_wires = list(range(len(wires)))

        wire_map = dict(zip(wires, contig_wires))

        [tape], _ = qml.map_wires(tape, wire_map)

        self._program = tape

    def reverse_qubit_order(self) -> None:
        """Reverses the wire ordering of a Pennylane tape."""
        tape = self.program.copy()

        wires_rev = sorted(tape.wires)
        wires = wires_rev.copy()
        wires_rev.reverse()

        wire_map = dict(zip(wires, wires_rev))

        [tape], _ = qml.map_wires(tape, wire_map)

        self._program = tape

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
Module defining PennylaneTape Class

"""
from typing import TYPE_CHECKING, List

import pennylane as qml
from pennylane.tape import QuantumTape

from qbraid.programs.abc_program import QuantumProgram

if TYPE_CHECKING:
    import numpy as np


class PennylaneTape(QuantumProgram):
    """Wrapper class for Pennylane Quantum Tape programs."""

    def __init__(self, program: QuantumTape):
        super().__init__(program)

    @property
    def program(self) -> QuantumTape:
        return self._program

    @program.setter
    def program(self, value: QuantumTape) -> None:
        if not isinstance(value, QuantumTape):
            raise ValueError("Program must be an instance of qml.tape.QuantumTape")
        self._program = value

    @property
    def qubits(self) -> List[int]:
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
        return qml.matrix(self.program)

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

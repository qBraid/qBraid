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
Module defining BraketCircuit Class

"""
from typing import TYPE_CHECKING

from braket.circuits import Circuit, Instruction, Qubit

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram

if TYPE_CHECKING:
    import braket.circuits
    import numpy as np


class BraketCircuit(GateModelProgram):
    """Wrapper class for ``braket.circuits.Circuit`` objects."""

    def __init__(self, program: "braket.circuits.Circuit"):
        super().__init__(program)
        if not isinstance(program, Circuit):
            raise ProgramTypeError(
                message=f"Expected 'braket.circuits.Circuit' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[Qubit]:
        """Return the qubits acted upon by the operations in this circuit"""
        return list(self.program.qubits)

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return self.program.qubit_count

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return 0

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        return self.program.depth

    def _unitary(self) -> "np.ndarray":
        """Calculate unitary of circuit."""
        return self.program.to_unitary()

    def populate_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, adds identity gates to vacant registers as needed."""
        max_qubit = 0
        occupied_qubits = []
        circuit = self.program.copy()
        for qubit in circuit.qubits:
            index = int(qubit)
            occupied_qubits.append(index)
            max_qubit = max(max_qubit, index)
        qubit_count = max_qubit + 1
        if qubit_count > circuit.qubit_count:
            all_qubits = list(range(0, qubit_count))
            vacant_qubits = list(set(all_qubits) - set(occupied_qubits))
            for index in vacant_qubits:
                circuit.i(index)
        self._program = circuit

    def remove_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        qubit_map = {}
        circuit = self.program.copy()
        circuit_qubits = list(circuit.qubits)
        circuit_qubits.sort()
        for index, qubit in enumerate(circuit_qubits):
            qubit_map[int(qubit)] = index
        contig_circuit = Circuit()
        for instr in circuit.instructions:
            contig_target = [qubit_map[int(qubit)] for qubit in list(instr.target)]
            contig_control = [qubit_map[int(qubit)] for qubit in list(instr.control)]
            contig_instr = Instruction(
                instr.operator,
                target=contig_target,
                control=contig_control,
                control_state=instr.control_state,
                power=instr.power,
            )
            contig_circuit.add_instruction(contig_instr)
        self._program = contig_circuit

    def reverse_qubit_order(self) -> None:
        """Reverse the order of the qubits in the circuit."""
        qubit_map = {}
        circuit = self.program.copy()
        circuit_qubits = list(circuit.qubits)
        circuit_qubits.sort()
        circuit_qubits = list(reversed(circuit_qubits))
        for index, qubit in enumerate(circuit_qubits):
            qubit_map[int(qubit)] = index
        contig_circuit = Circuit()
        for instr in circuit.instructions:
            contig_target = [qubit_map[int(qubit)] for qubit in list(instr.target)]
            contig_control = [qubit_map[int(qubit)] for qubit in list(instr.control)]
            contig_instr = Instruction(
                instr.operator,
                target=contig_target,
                control=contig_control,
                control_state=instr.control_state,
                power=instr.power,
            )
            contig_circuit.add_instruction(contig_instr)
        self._program = contig_circuit

    def transform(self, device) -> None:
        """Transform program to according to device target profile."""
        if device.simulator:
            self.remove_idle_qubits()

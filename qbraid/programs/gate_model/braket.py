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
from __future__ import annotations

from typing import TYPE_CHECKING

from braket.circuits import Circuit, Instruction, Qubit
from braket.circuits.measure import Measure

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram

if TYPE_CHECKING:
    import braket.circuits
    import numpy as np


class BraketCircuit(GateModelProgram):
    """Wrapper class for ``braket.circuits.Circuit`` objects."""

    def __init__(self, program: braket.circuits.Circuit):
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

    def _unitary(self) -> np.ndarray:
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

    def pad_measurements(self) -> None:
        """
        Pad the circuit with measurements on all qubits and track partial measurements.

        It adds partial measurement support to device that requires measuring all qubits
        (e.g., IonQ devices).

        This method identifies qubits that already have measurement instructions (partial
        measurements) and adds measurement instructions to all remaining qubits. It stores
        the list of originally measured qubits as an attribute for later use in result
        processing.

        The method modifies the circuit in-place and sets the `partial_measurement_qubits`
        attribute on the program object to track which qubits were originally measured
        before padding. The padding only occur when there is partial measurement in a
        circuit. If there is no measurement int the circuit, the backend assumes measuring
        all qubits and no padding is applied.
        """
        # Track qubits that already have measurement instructions
        partial_measurement_qubits: list[int] = []
        for instruction in self._program.instructions:
            if isinstance(instruction.operator, Measure):
                partial_measurement_qubits.append(int(instruction.target[0]))

        # Only apply padding when there is partial measurement
        if len(partial_measurement_qubits) == 0:
            return

        # Add measurements to all qubits that don't already have them
        for qubit in self._program.qubits:
            if qubit not in partial_measurement_qubits:
                self._program.measure(qubit)

        # Store the original partial measurement qubits for result processing
        self._program.partial_measurement_qubits = partial_measurement_qubits

    def transform(self, device) -> None:
        """Transform program to according to device target profile."""
        if device.simulator:
            self.remove_idle_qubits()

        # For IonQ and Amazon Braket simulators, pad measurements to support partial measurement
        if device._provider_name in ["IonQ", "Amazon Braket"]:
            self.pad_measurements()

    def serialize(self) -> dict[str, str]:
        """Return the program in a format suitable for submission to the qBraid API."""
        # pylint: disable=import-outside-toplevel
        from qbraid.programs.gate_model.qasm3 import OpenQasm3Program
        from qbraid.transpiler.conversions.braket import braket_to_qasm3

        # pylint: enable=import-outside-toplevel

        qasm = braket_to_qasm3(self.program)
        program = OpenQasm3Program(qasm)

        return program.serialize()

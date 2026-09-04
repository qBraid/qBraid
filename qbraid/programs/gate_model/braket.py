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
Module defining BraketCircuit Class

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from braket.circuits import Circuit, Instruction, Qubit
from braket.circuits.measure import Measure
from qbraid_core.services.runtime.schemas import Program

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
        measurements) and adds measurement instructions to all remaining qubits from qubit 0
        to qubit N, where N is the highest qubit index. A measurement is added even if a
        qubit has no gate. The list of originally measured qubits is stored as an attribute
        for later use in the result processing.

        The method modifies the circuit in-place and sets the `partial_measurement_qubits`
        attribute on the program object to track which qubits were originally measured
        before padding. The padding only occur when there is partial measurement in a
        circuit. If there is no measurement int the circuit, the backend assumes measuring
        all qubits and no padding is applied.
        """
        # Track qubits that already have measurement instructions
        existing_measures = [
            instruction
            for instruction in self._program.instructions
            if isinstance(instruction.operator, Measure)
        ]
        partial_measurement_qubits: list[int] = [
            int(instruction.target[0]) for instruction in existing_measures
        ]

        # Only apply padding when there is partial measurement or there is non-continguous qubits
        if (
            len(partial_measurement_qubits) == 0
            and max(self._program.qubits) + 1 == self._program.qubit_count
        ):
            return

        qubits_to_pad = [
            qubit
            for qubit in range(max(self._program.qubits) + 1)
            if qubit not in partial_measurement_qubits
        ]

        # A Braket ``Measure`` carries a ``_target_index`` that becomes the classical bit slot
        # when the circuit is serialized back to QASM. Three failure modes can silently corrupt
        # the emitted program, and we need to detect all of them before adding padded measures:
        #
        # 1. Internal collision. ``Circuit.from_ir`` reads each measure's target index literally
        #    from the source, so a program using multiple classical registers (e.g.
        #    ``a[0] = measure q[0]`` and ``b[0] = measure q[2]``) lands with two measures sharing
        #    ``_target_index == 0`` and one will clobber the other on serialization.
        # 2. Padding collision. ``Circuit.measure(q)`` does not use ``q`` as the bit index; it
        #    assigns ``_target_index = len(_measure_targets)``, a running counter. The padded
        #    measures we are about to add will therefore land on indices
        #    ``[k, k+1, ..., k+m-1]`` where ``k`` is the current measure count and ``m`` is the
        #    number of qubits to pad. If any existing measure already sits in that range, it
        #    collides with a padded measure.
        # 3. Out-of-range index. Braket emits ``bit[qubit_count] b`` regardless of the target
        #    indices, so any existing measure with ``_target_index >= qubit_count`` produces
        #    invalid QASM.
        #
        # When any of these would corrupt the output, rebase every existing measure to a
        # sequential ``[0, 1, ..., k-1]`` in instruction order. That leaves ``[k, k+m-1]`` free
        # for the padded measures (matching Braket's counter) and keeps every index under
        # ``qubit_count``. Circuits whose user-supplied bit labels are already safe are left
        # untouched so ``b[5] = measure q[0]`` round-trips as written.
        existing_indices = [m.operator._target_index for m in existing_measures]
        qubit_count = self._program.qubit_count
        padded_index_range = range(
            len(existing_measures), len(existing_measures) + len(qubits_to_pad)
        )
        has_internal_collision = len(set(existing_indices)) != len(existing_indices)
        has_padding_collision = any(idx in padded_index_range for idx in existing_indices)
        has_out_of_range = any(idx >= qubit_count for idx in existing_indices)
        if has_internal_collision or has_padding_collision or has_out_of_range:
            for new_index, measure in enumerate(existing_measures):
                measure.operator._target_index = new_index

        # Add measurements on qubit 0 to N if any of them doesn't already have a
        # measurement. N is the highest qubit index in the circuit.
        for qubit in qubits_to_pad:
            self._program.measure(qubit)

        # Store the original partial measurement qubits for result processing
        self._program.partial_measurement_qubits = partial_measurement_qubits

    def replace_i_with_rz_zero(self) -> None:
        """Replace all 'i' gates with 'rz(0)' gates in the circuit.

        This transformation is useful for IonQ devices that may not support
        the identity gate directly but can handle rz gates with zero angle.
        """
        circuit: Circuit = self.program.copy()
        new_circuit = Circuit()

        for instruction in circuit.instructions:
            if instruction.operator.name.lower() == "i":
                for target_qubit in instruction.target:
                    new_circuit.rz(target_qubit, 0)
            else:
                new_circuit.add_instruction(instruction)

        self._program = new_circuit

    def transform(self, device) -> None:
        """Transform program to according to device target profile."""
        if device.simulator:
            self.remove_idle_qubits()

        if device.profile.provider_name is not None:
            # For IonQ devices, replace identity gates with rz(0) gates
            if device.profile.provider_name.lower() == "ionq":
                self.replace_i_with_rz_zero()

            # For IonQ and Amazon Braket simulators, pad measurements to support partial measurement
            if device.profile.provider_name.lower() in {"ionq", "amazon braket"}:
                self.pad_measurements()

    def serialize(self) -> Program:
        """Return the program in a format suitable for submission to the qBraid API."""
        # pylint: disable=import-outside-toplevel
        from qbraid.programs.gate_model.qasm3 import OpenQasm3Program
        from qbraid.transpiler.conversions.braket import braket_to_qasm3

        # pylint: enable=import-outside-toplevel

        qasm = braket_to_qasm3(self.program)
        program = OpenQasm3Program(qasm)

        return program.serialize()

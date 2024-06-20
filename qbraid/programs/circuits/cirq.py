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
Module defining CirqCircuit Class

"""

import cirq
import numpy as np

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram


class CirqCircuit(GateModelProgram):
    """Wrapper class for ``cirq.Circuit`` objects."""

    def __init__(self, program: "cirq.Circuit"):
        super().__init__(program)
        if not isinstance(program, cirq.Circuit):
            raise ProgramTypeError(
                message=f"Expected 'cirq.Circuit' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[cirq.Qid]:
        """Return the qubits acted upon by the operations in this circuit"""
        return list(self.program.all_qubits())

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return 0

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        return len(cirq.Circuit(self.program.all_operations()))

    def _unitary(self) -> np.ndarray:
        """Calculate unitary of circuit."""
        return self.program.unitary()

    @staticmethod
    def is_measurement_gate(op: cirq.Operation) -> bool:
        """Returns whether Cirq gate/operation is MeasurementGate."""
        return isinstance(op, cirq.ops.MeasurementGate) or isinstance(
            getattr(op, "gate", None), cirq.ops.MeasurementGate
        )

    @staticmethod
    def _key_from_qubit(qubit: cirq.Qid) -> str:
        if isinstance(qubit, cirq.LineQubit):
            key = str(qubit)
        elif isinstance(qubit, cirq.GridQubit):
            key = str(qubit.row)
        elif isinstance(qubit, cirq.NamedQubit):
            # Only correct if numbered sequentially
            key = str(qubit.name)
        else:
            raise ValueError(
                "Expected qubit of type 'GridQubit' 'LineQubit' or 'NamedQubit'"
                f"but instead got {type(qubit)}"
            )
        return key

    @staticmethod
    def _int_from_qubit(qubit: cirq.Qid) -> int:
        """Extracts an integer value from a given qubit.

        This function interprets the qubit based on its type and extracts an
        integer value accordingly. For a LineQubit, it returns its index.
        For a GridQubit, it returns the row number. For a NamedQubit, it attempts
        to parse and return an integer value from its name. This parsing is only
        successful if the name of the NamedQubit contains an integer. If the name
        does not contain an integer, such as in the case of NamedQubit("q"), or if
        the qubit is not of the supported types (LineQubit, GridQubit, or NamedQubit),
        a ValueError is raised.

        Args:
            qubit (cirq.Qid): The qubit from which to extract an integer.

        Returns:
            int: The extracted integer value from the qubit.

        Raises:
            ValueError: If the qubit is a NamedQubit whose name does not contain
                        an integer, or if the qubit is not of a supported
                        type (LineQubit, GridQubit, or NamedQubit).
        """
        if isinstance(qubit, cirq.LineQubit):
            return int(qubit)
        if isinstance(qubit, cirq.GridQubit):
            return qubit.row
        if isinstance(qubit, cirq.NamedQubit):
            try:
                # NamedQubit("q") will fail here
                return int(qubit._comparison_key().split(":")[0][7:])
            except ValueError as err:
                raise ValueError(
                    f"The provided NamedQubit '{qubit.name}' cannot be converted to an integer."
                ) from err
        else:
            raise ValueError(
                "Expected qubit of type 'GridQubit' 'LineQubit' or 'NamedQubit'"
                f"but instead got {type(qubit)}"
            )

    @staticmethod
    def _make_qubits(qubits: list[cirq.Qid], targets: list[int]) -> list[cirq.Qid]:
        if len(set(type(qubit) for qubit in qubits)) > 1:
            # If mixed types, default to LineQubits
            qubit_type = cirq.LineQubit
        else:
            qubit_type = type(qubits[0])

        if qubit_type == cirq.LineQubit:
            return [cirq.LineQubit(i) for i in targets]
        if qubit_type == cirq.GridQubit:
            rows = [qubit.row for qubit in qubits]
            cols = [qubit.col for qubit in qubits]

            if len(set(rows)) == 1:
                # All qubits in a single row, vary column
                return [cirq.GridQubit(rows[0], i) for i in targets]
            if len(set(cols)) == 1:
                # All qubits in a single column, vary row
                return [cirq.GridQubit(i, cols[0]) for i in targets]

            raise ValueError("GridQubits must be aligned in a single row or column.")
        if qubit_type == cirq.NamedQubit:
            return [cirq.NamedQubit(str(i)) for i in targets]

        raise ValueError(
            f"Expected qubits of type 'GridQubit', 'LineQubit', 'NamedQubit' but got {qubit_type}"
        )

    def _convert_to_line_qubits(self) -> None:
        """Converts a Cirq circuit constructed using NamedQubits to
        a Cirq circuit constructed using LineQubits."""
        qubits = sorted(self.qubits)
        num_grid_qubits = sum(isinstance(qubit, cirq.GridQubit) for qubit in qubits)

        # Check if all qubits are GridQubits
        if len(qubits) == num_grid_qubits:
            rows, cols = zip(
                *((qubit.row, qubit.col) for qubit in qubits if isinstance(qubit, cirq.GridQubit))
            )

            rows_all_equal = len(set(rows)) == 1
            cols_all_equal = len(set(cols)) == 1

            if rows_all_equal:
                qubit_map = {qubit: cirq.LineQubit(qubit.col) for qubit in qubits}
            elif cols_all_equal:
                qubit_map = {qubit: cirq.LineQubit(qubit.row) for qubit in qubits}
            else:
                qubit_map = {qubit: cirq.LineQubit(i) for i, qubit in enumerate(qubits)}
        else:
            qubit_map = {}
            for i, qubit in enumerate(qubits):
                try:
                    qubit_map[qubit] = cirq.LineQubit(self._int_from_qubit(qubit))
                except ValueError:
                    # If _int_from_qubit fails, fallback to default contiguous qubit mapping
                    qubit_map = {qubit: cirq.LineQubit(i) for i, qubit in enumerate(qubits)}
                    break

        self._program = self.program.transform_qubits(lambda q: qubit_map[q])

    def populate_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, adds identity gates to vacant registers as needed."""
        circuit = self.program.copy()
        cirq_qubits = list(circuit.all_qubits())
        if any(isinstance(qubit, cirq.NamedQubit) for qubit in cirq_qubits):
            self._convert_to_line_qubits()
            self.populate_idle_qubits()
        else:
            nqubits = 0
            max_qubit = 0
            occupied_qubits = []
            for qubit in circuit.all_qubits():
                index = self._int_from_qubit(qubit)
                occupied_qubits.append(index)
                max_qubit = max(max_qubit, index)
                nqubits += 1
            qubit_count = max_qubit + 1
            if qubit_count > nqubits:
                all_qubits = list(range(0, qubit_count))
                vacant_qubits = list(set(all_qubits) - set(occupied_qubits))
                cirq_qubits = self._make_qubits(cirq_qubits, vacant_qubits)
                for qubit in cirq_qubits:
                    circuit.append(cirq.I(qubit))
            self._program = circuit

    def remove_idle_qubits(self) -> None:
        """If circuit does not use contiguous qubits/indices, reduces dimension accordingly."""
        qubits = sorted(self.qubits)
        qubit_map = dict(zip(qubits, self._make_qubits(qubits, range(len(qubits)))))
        self._program = self.program.transform_qubits(lambda q: qubit_map[q])

    def reverse_qubit_order(self) -> None:
        """Rerverse qubit ordering of circuit."""
        qubits = self.qubits
        qubits.sort()
        qubits_rev = qubits.copy()
        qubits_rev.reverse()
        qubit_map = dict(zip(qubits, qubits_rev))
        self._program = self.program.transform_qubits(lambda q: qubit_map[q])

    @staticmethod
    def remove_measurements(circuit: cirq.Circuit) -> cirq.Circuit:
        """Remove all measurement gates from the given Cirq circuit.

        Args:
            circuit (cirq.Circuit): The input circuit from which to remove measurement gates.

        Returns:
            cirq.Circuit: A new circuit with all measurement gates removed.
        """
        new_circuit = cirq.Circuit()
        for mom in circuit:
            filtered_operations = [
                op for op in mom.operations if not isinstance(op.gate, cirq.MeasurementGate)
            ]
            if filtered_operations:
                new_circuit.append(cirq.Moment(filtered_operations))
        return new_circuit

    @staticmethod
    def align_final_measurements(circuit: cirq.Circuit) -> cirq.Circuit:
        """
        Align the final measurement gates of all qubits in the same moment
        if they all end with a measurement.

        Args:
            circuit (cirq.Circuit): The input quantum circuit.

        Returns:
            cirq.Circuit: New circuit where all final measurements are aligned in the same moment.
        """
        new_circuit = cirq.Circuit()

        last_ops = {qubit: None for qubit in circuit.all_qubits()}

        for moment in circuit:
            for op in moment.operations:
                if isinstance(op.gate, cirq.MeasurementGate):
                    last_ops[op.qubits[0]] = op

        if all(op is not None for op in last_ops.values()):
            measurement_moment = cirq.Moment()
            for op in last_ops.values():
                measurement_moment = measurement_moment.with_operation(op)
            for moment in circuit:
                non_measurement_moment = cirq.Moment()
                for op in moment.operations:
                    if not isinstance(op.gate, cirq.MeasurementGate):
                        non_measurement_moment = non_measurement_moment.with_operation(op)
                if non_measurement_moment.operations:
                    new_circuit.append(non_measurement_moment)
            new_circuit.append(measurement_moment)
        else:
            return circuit

        return new_circuit

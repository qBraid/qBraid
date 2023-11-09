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
Module defining CirqCircuit Class

"""

from typing import List

import cirq
import numpy as np

from qbraid.programs.abc_program import QuantumProgram


class CirqCircuit(QuantumProgram):
    """Wrapper class for ``cirq.Circuit`` objects."""

    @property
    def program(self) -> cirq.Circuit:
        return self._program

    @program.setter
    def program(self, value: cirq.Circuit) -> None:
        if not isinstance(value, cirq.Circuit):
            raise ValueError("Program must be an instance of cirq.Circuit")
        self._program = value

    @property
    def qubits(self) -> List[cirq.Qid]:
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
        if isinstance(qubit, cirq.LineQubit):
            index = int(qubit)
        elif isinstance(qubit, cirq.GridQubit):
            index = qubit.row
        elif isinstance(qubit, cirq.NamedQubit):
            # Only correct if numbered sequentially
            index = int(qubit._comparison_key().split(":")[0][7:])
        else:
            raise ValueError(
                "Expected qubit of type 'GridQubit' 'LineQubit' or 'NamedQubit'"
                f"but instead got {type(qubit)}"
            )
        return index

    @staticmethod
    def _make_qubits(qubits: List[cirq.Qid], targets: List[int]) -> List[cirq.Qid]:
        if len(set(type(qubit) for qubit in qubits)) > 1:
            # If mixed types, default to LineQubits
            qubit_type = cirq.LineQubit
        else:
            qubit_type = type(qubits[0])

        if qubit_type == cirq.LineQubit:
            return [cirq.LineQubit(i) for i in targets]
        if qubit_type == cirq.GridQubit:
            return [cirq.GridQubit(0, i) for i in targets]
        if qubit_type == cirq.NamedQubit:
            return [cirq.NamedQubit(str(i)) for i in targets]
        raise ValueError(
            "Expected qubits of type 'GridQubit', 'LineQubit', or "
            f"'NamedQubit' but instead got {qubit_type}"
        )

    def _convert_to_line_qubits(self) -> None:
        """Converts a Cirq circuit constructed using NamedQubits to
        a Cirq circuit constructed using LineQubits."""
        qubits = list(self.program.all_qubits())
        qubits.sort()
        qubit_map = {self._key_from_qubit(q): i for i, q in enumerate(qubits)}
        line_qubit_circuit = cirq.Circuit()
        for opr in self.program.all_operations():
            qubit_indicies = [qubit_map[self._key_from_qubit(q)] for q in opr.qubits]
            line_qubits = [cirq.LineQubit(i) for i in qubit_indicies]
            line_qubit_circuit.append(opr.gate.on(*line_qubits))
        self._program = line_qubit_circuit

    def _contiguous_expansion(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, adds identity gates to vacant registers as needed."""
        circuit = self.program.copy()
        cirq_qubits = list(circuit.all_qubits())
        if isinstance(cirq_qubits[0], cirq.NamedQubit):
            self._convert_to_line_qubits()
            return

        nqubits = 0
        max_qubit = 0
        occupied_qubits = []
        for qubit in circuit.all_qubits():
            index = self._int_from_qubit(qubit)
            occupied_qubits.append(index)
            if index > max_qubit:
                max_qubit = index
            nqubits += 1
        qubit_count = max_qubit + 1
        if qubit_count > nqubits:
            all_qubits = list(range(0, qubit_count))
            vacant_qubits = list(set(all_qubits) - set(occupied_qubits))
            cirq_qubits = self._make_qubits(cirq_qubits, vacant_qubits)
            for qubit in cirq_qubits:
                circuit.append(cirq.I(qubit))
        self._program = circuit
        return

    def _contiguous_compression(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        original_qubits = sorted(self.program.all_qubits(), key=self._int_from_qubit)
        qubit_map = dict(
            zip(original_qubits, self._make_qubits(original_qubits, range(len(original_qubits))))
        )
        self._program = self.program.transform_qubits(lambda q: qubit_map[q])

    def reverse_qubit_order(self) -> None:
        """Rerverse qubit ordering of circuit."""
        original_qubits = sorted(self.program.all_qubits(), key=self._int_from_qubit)
        max_index = max(self._int_from_qubit(q) for q in original_qubits)
        qubit_map = dict(
            zip(original_qubits, self._make_qubits(original_qubits, reversed(range(max_index + 1))))
        )
        self._program = self.program.transform_qubits(lambda q: qubit_map[q])

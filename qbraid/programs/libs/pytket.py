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
Module defining PytketCircuit Class

"""

from typing import TYPE_CHECKING, List, Optional, Union

import numpy as np
from pytket.circuit import Circuit, Command, OpType
from pytket.unit_id import Qubit

from qbraid.programs.abc_program import QuantumProgram

if TYPE_CHECKING:
    import pytket


class PytketCircuit(QuantumProgram):
    """Wrapper class for ``pytket.circuit.Circuit`` objects."""

    def __init__(self, program: "pytket.Circuit"):
        super().__init__(program)

    @property
    def program(self) -> Circuit:
        return self._program

    @program.setter
    def program(self, value: Circuit) -> None:
        if not isinstance(value, Circuit):
            raise ValueError("Program must be an instance of pytket.circuit.Circuit")
        self._program = value

    @property
    def qubits(self) -> List[Qubit]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self.program.qubits

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return self.program.n_qubits

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return self.program.n_bits

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        return self.program.depth()

    @staticmethod
    def remove_measurements(original_circuit):
        """
        Return a new circuit with all non-measurement operations from the original circuit.

        Args:
            original_circuit: The pytket Circuit to process.

        Returns:
            A new pytket Circuit without measurement operations.
        """
        new_circuit = Circuit()
        for qreg in original_circuit.qubits:
            new_circuit.add_qubit(qreg)
        for creg in original_circuit.bits:
            new_circuit.add_bit(creg)

        for command in original_circuit.get_commands():
            if command.op.type != OpType.Measure:
                new_circuit.add_gate(
                    command.op.type, command.op.params, [q.index[0] for q in command.qubits]
                )

        return new_circuit

    def _unitary(self) -> "np.ndarray":
        """Return the unitary of a pytket circuit."""
        try:
            return self.program.get_unitary()
        except RuntimeError:
            program_copy = self.remove_measurements(self.program)
            return program_copy.get_unitary()

    def remove_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        circuit = self.program.copy()
        circuit.remove_blank_wires()
        self._program = circuit

    def reverse_qubit_order(self) -> None:
        """Reverses the qubit ordering of a PyTKET circuit."""
        new_c = Circuit(self.num_qubits)
        for gate in self.program.get_commands():
            circuit_qubits = gate.qubits
            circuit_qubits = [(self.num_qubits - 1) - qubits.index[0] for qubits in circuit_qubits]
            gate_op = gate.op
            # devide parameter by pi, from radian to degree
            new_c.add_gate(
                gate_op.type,
                np.array(gate_op.params) / np.pi if gate_op.params else gate_op.params,
                circuit_qubits,
            )
        self._program = new_c

    @staticmethod
    def gate_to_matrix(
        gates: Optional[Union[List[Circuit], Command]], flat: bool = False
    ) -> np.ndarray:
        """Return the unitary of the Command"""
        gates = gates if (list == type(gates)) else [gates]
        a = list(map(max, [gate.qubits for gate in gates]))
        circuit = Circuit(max(a).index[0] + 1)
        for gate in gates:
            gate_op = gate.op
            circuit.add_gate(gate_op.type, gate_op.params, gate.qubits)
        if flat:
            circuit.remove_blank_wires()
        return circuit.get_unitary()

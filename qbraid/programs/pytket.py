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

from typing import List, Optional, Union

import numpy as np
from pytket.circuit import Circuit, Command
from pytket.unit_id import Qubit

from qbraid.programs.abc_program import QuantumProgram


class PytketCircuit(QuantumProgram):
    """Wrapper class for ``pytket.circuit.Circuit`` objects."""

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

    def _unitary(self) -> "np.ndarray":
        """Return the unitary of a pytket circuit."""
        return self.program.get_unitary()

    def _contiguous_expansion(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, adds identity gates to vacant registers as needed."""
        raise NotImplementedError

    def _contiguous_compression(self) -> None:
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

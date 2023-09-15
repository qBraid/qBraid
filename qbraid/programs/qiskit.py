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
Module defining QiskitCircuit Class

"""

from collections import OrderedDict
from typing import TYPE_CHECKING, List

import qiskit
from qiskit.circuit import Qubit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.quantum_info import Operator

from qbraid.programs.abc_program import QuantumProgram

if TYPE_CHECKING:
    import numpy as np


class QiskitCircuit(QuantumProgram):
    """Wrapper class for ``qiskit.QuantumCircuit`` objects"""

    @property
    def program(self) -> qiskit.QuantumCircuit:
        return self._program

    @program.setter
    def program(self, value: qiskit.QuantumCircuit) -> None:
        if not isinstance(value, qiskit.QuantumCircuit):
            raise ValueError("Program must be an instance of qiskit.QuantumCircuit")
        self._program = value

    @property
    def qubits(self) -> List[Qubit]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self.program.qubits

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return self.program.num_qubits

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return self.program.num_clbits

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        return self.program.depth()

    def _unitary(self) -> "np.ndarray":
        """Calculate unitary of circuit."""
        return Operator(self.program).data

    def _contiguous_expansion(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, adds identity gates to vacant registers as needed."""
        raise NotImplementedError

    def _contiguous_compression(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        circuit = self.program.copy()

        dag = circuit_to_dag(circuit)

        idle_wires = list(dag.idle_wires())
        for w in idle_wires:
            dag._remove_idle_wire(w)
            dag.qubits.remove(w)

        dag.qregs = OrderedDict()

        self._program = dag_to_circuit(dag)

    def reverse_qubit_order(self) -> None:
        """Reverse the order of the qubits in the circuit."""
        circuit = self.program.copy()
        reversed_circuit = qiskit.QuantumCircuit(circuit.num_qubits)

        for inst, qargs, _ in circuit.data:
            # Find the index of the qubit within the circuit using the `find_bit` method
            qubit_indices = [circuit.qubits.index(qubit) for qubit in qargs]
            # Reverse the qubit indices for the instruction
            reversed_qargs = [circuit.num_qubits - 1 - idx for idx in qubit_indices]
            reversed_circuit.append(inst, reversed_qargs)

        self._program = reversed_circuit

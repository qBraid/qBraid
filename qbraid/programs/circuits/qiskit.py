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
Module defining QiskitCircuit Class

"""
from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING

import qiskit
from qiskit.circuit import Qubit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.quantum_info import Operator

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram

if TYPE_CHECKING:
    import numpy as np


class QiskitCircuit(GateModelProgram):
    """Wrapper class for ``qiskit.QuantumCircuit`` objects"""

    def __init__(self, program: qiskit.QuantumCircuit):
        super().__init__(program)
        if not isinstance(program, qiskit.QuantumCircuit):
            raise ProgramTypeError(
                message=f"Expected 'qiskit.QuantumCircuit' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[Qubit]:
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

    def _unitary(self) -> np.ndarray:
        """Calculate unitary of circuit. Removes measurement gates to
        perform calculation if necessary."""
        circuit = self.program.copy()
        circuit.remove_final_measurements()
        return Operator(circuit).data

    def remove_idle_qubits(self) -> None:
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
        reversed_circuit = circuit.reverse_bits()
        self._program = reversed_circuit

    def transform(self, device) -> None:
        """Transform program to according to device target profile."""
        if getattr(device.profile, "local", False) is True:
            self.remove_idle_qubits()

        self._program = qiskit.transpile(self.program, backend=device._backend)

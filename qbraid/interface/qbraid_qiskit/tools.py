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
Module containing Qiskit tools

"""
from collections import OrderedDict

import numpy as np
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.quantum_info import Operator

QASMType = str


def reverse_qubit_ordering(circuit: QuantumCircuit) -> QuantumCircuit:
    """Reverses the qubit ordering of a Qiskit circuit."""
    num_qubits = circuit.num_qubits
    reversed_circuit = QuantumCircuit(num_qubits)

    for inst, qargs, _ in circuit.data:
        # Find the index of the qubit within the circuit using the `find_bit` method
        qubit_indices = [circuit.qubits.index(qubit) for qubit in qargs]
        # Reverse the qubit indices for the instruction
        reversed_qargs = [num_qubits - 1 - idx for idx in qubit_indices]
        reversed_circuit.append(inst, reversed_qargs)

    return reversed_circuit


def _unitary_from_qiskit(circuit: QuantumCircuit) -> np.ndarray:
    """Return the unitary of a Qiskit quantum circuit."""
    return Operator(circuit).data


def _convert_to_contiguous_qiskit(circuit: QuantumCircuit, rev_qubits=False) -> QuantumCircuit:
    """Delete qubit(s) with no gate, if any exist."""
    circuit = reverse_qubit_ordering(circuit) if rev_qubits else circuit

    dag = circuit_to_dag(circuit)

    idle_wires = list(dag.idle_wires())
    for w in idle_wires:
        dag._remove_idle_wire(w)
        dag.qubits.remove(w)

    dag.qregs = OrderedDict()

    return dag_to_circuit(dag)

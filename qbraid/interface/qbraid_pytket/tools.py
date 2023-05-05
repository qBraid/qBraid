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
Module containing pyQuil tools

"""
from typing import List, Optional, Union

import numpy as np
from pytket.circuit import Circuit as TKCircuit
from pytket.circuit import Command as TKInstruction


def _unitary_from_pytket(circuit: TKCircuit) -> np.ndarray:
    """Return the unitary of a pytket circuit."""
    return circuit.get_unitary()


def _gate_to_matrix_pytket(
    gates: Optional[Union[List[TKInstruction], TKInstruction]], flat: bool = False
) -> np.ndarray:
    """Return the unitary of the Command"""
    gates = gates if (list == type(gates)) else [gates]
    a = list(map(max, [gate.qubits for gate in gates]))
    circuit = TKCircuit(max(a).index[0] + 1)
    for gate in gates:
        gate_op = gate.op
        circuit.add_gate(gate_op.type, gate_op.params, gate.qubits)
    if flat:
        circuit.remove_blank_wires()
    return circuit.get_unitary()


def _convert_to_contiguous_pytket(circuit: TKCircuit, rev_qubits=False) -> TKCircuit:
    """delete qubit with no gate and optional reverse circuit"""
    if rev_qubits:
        new_c = TKCircuit(circuit.n_qubits)
        for gate in circuit.get_commands():
            circuit_qubits = gate.qubits
            circuit_qubits = [(circuit.n_qubits - 1) - qubits.index[0] for qubits in circuit_qubits]
            gate_op = gate.op
            # devide parameter by pi, from radian to degree
            new_c.add_gate(
                gate_op.type,
                np.array(gate_op.params) / np.pi if gate_op.params else gate_op.params,
                circuit_qubits,
            )
        circuit = new_c
    circuit.remove_blank_wires()
    return circuit

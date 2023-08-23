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
Module containing Braket tools

"""
import numpy as np
from braket.circuits import Circuit as BKCircuit
from braket.circuits import Instruction


def _unitary_from_braket(circuit: BKCircuit) -> np.ndarray:
    """Return the little-endian unitary of a Braket circuit."""
    return circuit.to_unitary()


def _contiguous_expansion(circuit: BKCircuit) -> BKCircuit:
    """Checks whether the circuit uses contiguous qubits/indices,
    and if not, adds identity gates to vacant registers as needed."""
    max_qubit = 0
    occupied_qubits = []
    for qubit in circuit.qubits:
        index = int(qubit)
        occupied_qubits.append(index)
        if index > max_qubit:
            max_qubit = index
    qubit_count = max_qubit + 1
    if qubit_count > circuit.qubit_count:
        all_qubits = list(range(0, qubit_count))
        vacant_qubits = list(set(all_qubits) - set(occupied_qubits))
        for index in vacant_qubits:
            circuit.i(index)
    return circuit


def _contiguous_compression(circuit: BKCircuit, rev_qubits=False) -> BKCircuit:
    """Checks whether the circuit uses contiguous qubits/indices,
    and if not, reduces dimension accordingly."""
    qubit_map = {}
    circuit_qubits = list(circuit.qubits)
    circuit_qubits.sort()
    if rev_qubits:
        circuit_qubits = list(reversed(circuit_qubits))
    for index, qubit in enumerate(circuit_qubits):
        qubit_map[int(qubit)] = index
    contig_circuit = BKCircuit()
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
    return contig_circuit


def _convert_to_contiguous_braket(
    circuit: BKCircuit, rev_qubits=False, expansion=False
) -> BKCircuit:
    if expansion:
        return _contiguous_expansion(circuit)
    return _contiguous_compression(circuit, rev_qubits=rev_qubits)

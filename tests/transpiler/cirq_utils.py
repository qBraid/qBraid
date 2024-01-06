# Copyright (C) 2023 qBraid
# Copyright (C) Unitary Fund
#
# This file is part of the qBraid-SDK.
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# This file includes code adapted from Mitiq (https://github.com/unitaryfund/mitiq)
# with modifications by qBraid. The original copyright notice is included above.
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# qbraid: skip-header

"""
Module containing function to test Cirq circuit equality

"""
from copy import deepcopy

import cirq

import qbraid.programs.cirq


def _rev_qubits(circuit: cirq.Circuit) -> cirq.Circuit:
    """Reverses the qubit order of a circuit."""
    program = qbraid.programs.cirq.CirqCircuit(circuit)
    program.reverse_qubit_order()
    return program.program


def _equal(
    circuit_one: cirq.Circuit,
    circuit_two: cirq.Circuit,
    require_qubit_equality: bool = False,
    require_measurement_equality: bool = False,
    allow_reversed_qubit_order: bool = False,
) -> bool:
    """Returns True if the circuits are equal, else False.

    Args:
        circuit_one: Input circuit to compare to circuit_two.
        circuit_two: Input circuit to compare to circuit_one.
        require_qubit_equality: Requires that the qubits be equal
            in the two circuits.
        require_measurement_equality: Requires that measurements are equal on
            the two circuits, meaning that measurement keys are equal.
        allow_reversed_qubit_order: Allows considering the circuits as equal
            even if their qubit order is reversed. Default is False.

    Note:
        If set(circuit_one.all_qubits()) = {LineQubit(0)},
        then set(circuit_two_all_qubits()) must be {LineQubit(0)},
        else the two are not equal.
        If True, the qubits of both circuits must have a well-defined ordering.
    """
    # Make a deepcopy only if it's necessary
    if not (require_qubit_equality and require_measurement_equality):
        circuit_one = deepcopy(circuit_one)
        circuit_two = deepcopy(circuit_two)

    if not require_qubit_equality:
        # Transform the qubits of circuit one to those of circuit two
        qubit_map = dict(
            zip(
                sorted(circuit_one.all_qubits()),
                sorted(circuit_two.all_qubits()),
            )
        )
        circuit_one = circuit_one.transform_qubits(lambda q: qubit_map[q])

    if not require_measurement_equality:
        for circ in (circuit_one, circuit_two):
            measurements = [
                (moment, op)
                for moment, op, _ in circ.findall_operations_with_gate_type(cirq.MeasurementGate)
            ]
            circ.batch_remove(measurements)

    if allow_reversed_qubit_order and circuit_one != circuit_two:
        reversed_circuit_one = _rev_qubits(circuit_one)
        return _equal(
            reversed_circuit_one,
            circuit_two,
            require_qubit_equality,
            require_measurement_equality,
            False,
        )

    return circuit_one == circuit_two

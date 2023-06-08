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
Module containing Cirq utility functions

"""
from copy import deepcopy

from cirq import Circuit, MeasurementGate


def _equal(
    circuit_one: Circuit,
    circuit_two: Circuit,
    require_qubit_equality: bool = False,
    require_measurement_equality: bool = False,
) -> bool:
    
    """Compare two Cirq circuits for equality.

    Args:
        circuit_one: The first circuit to compare.
        circuit_two: The second circuit to compare.
        require_qubit_equality: If True, the qubits in both circuits must be equal.
        require_measurement_equality: If True, the measurements in both circuits must be equal.

    Returns:
        A boolean value indicating whether the two circuits are equal.

    Notes:
        - If `require_qubit_equality` is True, the qubits in both circuits must have the same
          elements, but their order can differ.
        - If `require_measurement_equality` is True, the measurements in both circuits must be
          equal, meaning their measurement keys must match.
        - If `require_qubit_equality` is False, the qubits of `circuit_one` are transformed to
          match the qubits of `circuit_two`. This assumes that the qubits have a well-defined
          ordering in both circuits.
        - If `require_measurement_equality` is False, all measurements are removed from both
          circuits before the comparison.

    Example:
        circuit1 = Circuit()
        circuit2 = Circuit()

        # Compare the circuits for equality, requiring qubit and measurement equality
        result = _equal(circuit1, circuit2, require_qubit_equality=True,
                        require_measurement_equality=True)
        print(result)  # True if the circuits are equal, False otherwise
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
                for moment, op, _ in circ.findall_operations_with_gate_type(MeasurementGate)
            ]
            circ.batch_remove(measurements)
    return circuit_one == circuit_two

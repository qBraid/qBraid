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
Unit tests for cirq transformations.

"""
import cirq

from qbraid.transforms.cirq.passes import align_final_measurements


def test_align_final_measurements():
    """Test aligning measurements for a circuit with measurements."""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, key="m0"), cirq.measure(q1, key="m1")
    )
    expected_circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.CNOT(q0, q1),
        cirq.Moment(cirq.measure(q0, key="m0"), cirq.measure(q1, key="m1")),
    )
    aligned_circuit = align_final_measurements(circuit)
    assert (
        aligned_circuit == expected_circuit
    ), "The measurements should be aligned in the same moment"


def test_align_measurements_for_no_measurement():
    """Test aligning measurements for a circuit with no measurements."""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    expected_circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    aligned_circuit = align_final_measurements(circuit)
    assert (
        aligned_circuit == expected_circuit
    ), "The circuit should remain unchanged as there are no measurements"


def test_align_measurements_for_partial_measurement():
    """Test aligning measurements from a circuit where not all qubits are measured."""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, key="m0"))
    expected_circuit = circuit
    aligned_circuit = align_final_measurements(circuit)
    assert (
        aligned_circuit == expected_circuit
    ), "The circuit should remain unchanged as not all qubits are measured"

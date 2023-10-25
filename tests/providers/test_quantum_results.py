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
Unit tests for retrieving and post-processing experimental results.

"""
import os

import pytest

from qbraid import device_wrapper
from qbraid.interface import random_circuit
from qbraid.providers.result import QuantumJobResult

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM/AWS storage)"


@pytest.mark.parametrize(
    "counts_raw, expected_out, include_zero_values",
    [
        ({" 1": 0, "0": 550}, {"0": 550}, False),
        ({"10": 479, "1 1": 13, "0 0 ": 496}, {"00": 496, "10": 479, "11": 13}, False),
        ({" 1": 474, "0": 550}, {"0": 550, "1": 474}, True),
        ({"10": 479, "1 1": 13, "0 0 ": 496}, {"00": 496, "01": 0, "10": 479, "11": 13}, True),
        (
            {"10 1": 586, "11  0  ": 139, "0 01": 496, "  010": 543, "11 1": 594},
            {
                "000": 0,
                "001": 496,
                "010": 543,
                "011": 0,
                "100": 0,
                "101": 586,
                "110": 139,
                "111": 594,
            },
            True,
        ),
    ],
)
def test_format_counts(counts_raw, expected_out, include_zero_values):
    """Test formatting of raw measurement counts."""
    counts_out = QuantumJobResult.format_counts(counts_raw, include_zero_values=include_zero_values)
    assert counts_out == expected_out  # check equivalance
    assert list(counts_out.items()) == list(expected_out.items())  # check ordering of keys


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
@pytest.mark.parametrize("device_id", ["ibm_q_simulator_statevector", "aws_sv_sim"])
def test_result_wrapper_measurements(device_id):
    """Test result wrapper measurements method."""
    circuit = random_circuit("qiskit", num_qubits=3, depth=3, measure=True)
    sim = device_wrapper(device_id).run(circuit, shots=10)
    qbraid_result = sim.result()
    counts = qbraid_result.measurement_counts()
    measurements = qbraid_result.measurements()
    assert isinstance(counts, dict)
    assert measurements.shape == (10, 3)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
@pytest.mark.parametrize("device_id", ["ibm_q_qasm_simulator", "ibm_q_simulator_statevector"])
def test_result_wrapper_batch_measurements(device_id):
    """Test result wrapper measurements method for circuit batch."""
    circuit = random_circuit("qiskit", num_qubits=3, depth=3, measure=True)
    sim = device_wrapper(device_id).run_batch([circuit, circuit, circuit], shots=10)
    qbraid_result = sim.result()
    counts = qbraid_result.measurement_counts()
    measurements = qbraid_result.measurements()

    assert isinstance(counts, list)
    for count in counts:
        assert isinstance(count, dict)

    assert measurements.shape == (3, 10, 3)

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
Unit tests for BracketQuantumTask class

"""
import os
from unittest.mock import Mock, patch

import pytest
from braket.circuits import Circuit
from braket.devices import LocalSimulator

from qbraid.runtime.braket.job import BraketQuantumTask

from .fixtures import SV1_ARN, device_wrapper_inputs, test_circuits

skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of AWS storage)"

inputs_braket_run = [SV1_ARN]
inputs_braket_dw = [] if skip_remote_tests else device_wrapper_inputs("AWS")
circuits_braket_run = test_circuits


def test_braket_queue_visibility():
    """Test methods that check Braket device/job queue."""
    with patch("qbraid.runtime.braket.BraketProvider") as _:
        circuit = Circuit().h(0).cnot(0, 1)

        mock_device = Mock()
        mock_job = Mock()
        mock_job.queue_position.return_value = 5  # job is 5th in queue

        mock_device.run.return_value = mock_job

        device = mock_device
        if device is None:
            pytest.skip("No devices available for testing")
        else:
            job = device.run(circuit, shots=10)
            queue_position = job.queue_position()
            job.cancel()
            assert isinstance(queue_position, int)


@patch("qbraid.runtime.braket.job.AwsQuantumTask")
def test_load_completed_job(mock_aws_quantum_task):
    """Test is terminal state method for BraketQuantumTask."""
    circuit = Circuit().h(0).cnot(0, 1)
    mock_device = LocalSimulator()
    mock_job = mock_device.run(circuit, shots=10)
    mock_aws_quantum_task.return_value = mock_job
    job = BraketQuantumTask(mock_job.id, task=None)
    assert job.metadata()["job_id"] == mock_job.id
    assert job.is_terminal_state()

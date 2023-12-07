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
Unit tests for Amazon Braket cost tracker interface

"""
import os
from decimal import Decimal

import pytest
from braket.circuits import Circuit
from braket.tracking import Tracker

from qbraid.providers.aws import BraketProvider
from qbraid.providers.aws.tracker import get_quantum_task_cost

# Skip tests if AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of AWS storage)"


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_quantum_task_cost_simulator():
    """Test getting cost of quantum task run on an AWS simulator."""
    provider = BraketProvider()
    device = provider.get_device("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
    circuit = Circuit().h(0).cnot(0, 1)

    with Tracker() as tracker:
        task = device.run(circuit, shots=2)
        task.result()

    expected = tracker.simulator_tasks_cost()
    calculated = get_quantum_task_cost(task.id, provider._get_aws_session())
    assert expected == calculated


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_quantum_task_cost_cancelled(braket_most_busy, braket_circuit):
    """Test getting cost of quantum task that was cancelled."""
    if braket_most_busy is None:
        pytest.skip("No AWS QPU devices available")

    provider = BraketProvider()

    # AwsSession region must match device region
    region_name = provider._get_region_name(braket_most_busy._id)
    aws_session = provider._get_aws_session(region_name)

    qbraid_job = braket_most_busy.run(braket_circuit, shots=10)
    qbraid_job.cancel()

    task_arn = qbraid_job.vendor_job_id

    # with pytest.raises(ValueError) as excinfo:
    #     get_quantum_task_cost(task_arn, aws_session)

    # assert "Current state is CANCELLING" in str(excinfo.value)

    qbraid_job.wait_for_final_state()
    assert get_quantum_task_cost(task_arn, aws_session) == Decimal(0)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_quantum_task_cost_region_mismatch(braket_most_busy, braket_circuit):
    """Test getting cost of quantum task raises value error on region mismatch."""
    if braket_most_busy is None:
        pytest.skip("No AWS QPU devices available")

    braket_device = braket_most_busy._device
    task = braket_device.run(braket_circuit, shots=10)
    task.cancel()

    task_arn = task.id
    task_region = task_arn.split(":")[3]
    other_region = "eu-west-2" if task_region == "us-east-1" else "us-east-1"

    provider = BraketProvider()
    aws_session = provider._get_aws_session(other_region)

    with pytest.raises(ValueError) as excinfo:
        get_quantum_task_cost(task_arn, aws_session)

    assert (
        str(excinfo.value)
        == f"AwsSession region {other_region} does not match task region {task_region}"
    )

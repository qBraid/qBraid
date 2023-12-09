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
Unit tests for BraketProvider class

"""
import os

import pytest
from braket.circuits import Circuit

from qbraid import device_wrapper, job_wrapper
from qbraid.providers.aws import BraketProvider

# Skip tests if AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of AWS storage)"


def get_braket_most_busy():
    """Return the most busy device for testing purposes."""
    provider = BraketProvider()
    braket_devices = provider.get_devices(
        types=["QPU"], statuses=["ONLINE"], provider_names=["Rigetti", "IonQ", "Oxford"]
    )
    qbraid_devices = [device_wrapper(device.arn) for device in braket_devices]
    test_device = None
    max_queued = 0
    for device in qbraid_devices:
        jobs_queued = device.queue_depth()
        if jobs_queued is not None and jobs_queued > max_queued:
            max_queued = jobs_queued
            test_device = device
    return test_device


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_braket_queue_visibility():
    """Test methods that check Braket device/job queue."""
    circuit = Circuit().h(0).cnot(0, 1)
    device = get_braket_most_busy()
    if device is None:
        pytest.skip("No devices available for testing")
    else:
        job = device.run(circuit, shots=10)
        queue_position = job.queue_position()
        job.cancel()
        assert isinstance(queue_position, int)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
@pytest.mark.parametrize(
    "company,region", [("rigetti", "us-west-1"), ("ionq", "us-east-1"), ("oqc", "eu-west-2")]
)
def test_get_region_name(company, region):
    """Test getting the AWS region name."""
    provider = BraketProvider()
    fake_arn = f"arn:aws:braket:::device/qpu/{company}/device"
    assert provider._get_region_name(fake_arn) == region


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_job_wrapper_type():
    """Test that job wrapper creates object of original job type"""
    device = device_wrapper("aws_dm_sim")
    circuit = Circuit().h(0).cnot(0, 1)
    job_0 = device.run(circuit, shots=10)
    job_1 = job_wrapper(job_0.id)
    assert isinstance(job_0, type(job_1))
    assert job_0.vendor_job_id == job_1.metadata()["vendorJobId"]

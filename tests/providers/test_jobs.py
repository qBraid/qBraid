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
Unit tests for managing Quantum Jobs

"""
import os

import pytest
from braket.circuits import Circuit

from qbraid import device_wrapper
from qbraid.providers.aws import BraketProvider

# Skip tests if IBM/AWS account auth/creds not configured
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
        jobs_queued = device.pending_jobs()
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

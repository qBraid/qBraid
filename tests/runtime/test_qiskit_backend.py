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
Unit tests for QiskitBackend class.

"""
import os

from typing import Union

import pytest
from qiskit.providers import Backend
from qiskit.providers.basic_provider.basic_provider_job import BasicProviderJob
from qiskit_aer.jobs.aerjob import AerJob

from qbraid.runtime.qiskit import QiskitBackend, QiskitJob

from .fixtures import test_circuits, fake_ibm_devices

# Skip tests if IBM account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM storage)"


inputs_qiskit_dw = fake_ibm_devices()
circuits_qiskit_run = test_circuits


@pytest.mark.parametrize("device", fake_ibm_devices())
def test_wrap_fake_provider(device):
    """Test wrapping fake Qiskit provider."""
    assert isinstance(device, QiskitBackend)
    assert isinstance(device._backend, Backend)


def test_queue_depth():
    """Test getting number of pending jobs for QiskitBackend."""
    ibm_device = fake_ibm_devices()[0]
    assert isinstance(ibm_device.queue_depth(), int)


@pytest.mark.parametrize("qbraid_device", fake_ibm_devices())
@pytest.mark.parametrize("circuit", circuits_qiskit_run)
def test_run_fake_qiskit_device_wrapper(qbraid_device, circuit):
    """Test run method from wrapped fake Qiskit backends"""
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, Union[BasicProviderJob, AerJob])


@pytest.mark.parametrize("qbraid_device", fake_ibm_devices())
def test_run_fake_batch_qiskit_device_wrapper(qbraid_device):
    """Test run method from wrapped fake Qiskit backends"""
    qbraid_job = qbraid_device.run(circuits_qiskit_run, shots=10)
    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, Union[BasicProviderJob, AerJob])

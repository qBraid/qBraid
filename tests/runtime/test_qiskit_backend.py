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
import random
import time
from typing import Union

import pytest
from unittest.mock import patch, Mock
from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.providers.basic_provider.basic_provider_job import BasicProviderJob
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit_aer.jobs.aerjob import AerJob
from qiskit_ibm_runtime import IBMBackend, RuntimeJob
from qiskit_ibm_runtime.qiskit_runtime_service import QiskitBackendNotFoundError

from qbraid.programs import ProgramSpec
from qbraid.runtime import DeviceType, JobStateError, TargetProfile
from qbraid.runtime.qiskit import QiskitBackend, QiskitJob, QiskitRuntimeProvider

from .fixtures import cirq_circuit, qiskit_circuit

# Skip tests if IBM account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM storage)"


class FakeService:
    """Fake Qiskit runtime service for testing."""
    def backend(self, backend_name, instance=None):
        """Return fake backend."""
        for backend in self.backends(instance=instance):
            if backend_name == backend.name:
                return backend
        raise QiskitBackendNotFoundError("No backend matches the criteria.")

    def backends(self, **kwargs):  # pylint: disable=unused-argument
        """Return fake Qiskit backend."""
        return [GenericBackendV2(num_qubits=5), GenericBackendV2(num_qubits=20)]

    def least_busy(self, **kwargs):
        """Return least busy backend."""
        return random.choice(self.backends(**kwargs))


def ibm_devices():
    """Get list of wrapped ibm backends for testing."""
    provider = QiskitRuntimeProvider()
    backends = provider.get_devices(
        filters=lambda b: b.status().status_msg == "active", operational=True
    )
    return [backend.id for backend in backends]


def fake_ibm_devices():
    """Get list of fake wrapped ibm backends for testing"""
    service = FakeService()
    backends = service.backends()
    program_spec = ProgramSpec(QuantumCircuit)
    profiles = [
        TargetProfile(backend.name, DeviceType.LOCAL_SIMULATOR, backend.num_qubits, program_spec)
        for backend in backends
    ]
    return [QiskitBackend(profile, service) for profile in profiles]


inputs_qiskit_dw = fake_ibm_devices()
circuits_qiskit_run = [cirq_circuit(), qiskit_circuit()]


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

@pytest.mark.parametrize("device", fake_ibm_devices())
def test_cancel_completed_batch_error(device):
    """Test that cancelling a batch job that has already reached its
    final state raises an error."""
    job = device.run(circuits_qiskit_run, shots=10)

    timeout = 30
    check_every = 2
    elapsed_time = 0

    while elapsed_time < timeout:
        if job.is_terminal_state():
            break

        time.sleep(check_every)
        elapsed_time += check_every

    if elapsed_time >= timeout:
        try:
            job.cancel()
        except JobStateError:
            pass

    with pytest.raises(JobStateError):
        job.cancel()

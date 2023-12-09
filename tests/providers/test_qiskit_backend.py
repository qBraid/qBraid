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
Unit tests for QiskitBackend class.

"""
import os
import time

import pytest
from qiskit.providers import Backend
from qiskit.providers.fake_provider import FakeManilaV2
from qiskit_ibm_provider import IBMBackend, IBMJob

from qbraid import device_wrapper
from qbraid.providers import QuantumJob
from qbraid.providers.exceptions import JobStateError
from qbraid.providers.ibm import QiskitBackend, QiskitJob, QiskitProvider

from .fixtures import cirq_circuit, device_wrapper_inputs, qiskit_circuit

# Skip tests if IBM account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM storage)"

### FIXTURES ###


def ibm_devices():
    """Get list of wrapped ibm backends for testing."""
    provider = QiskitProvider()
    backends = provider.get_devices(
        filters=lambda b: b.status().status_msg == "active", operational=True
    )
    qbraid_device_names = device_wrapper_inputs("IBM")
    ibm_device_names = [provider.ibm_to_qbraid_id(backend.name) for backend in backends]
    return [dev for dev in ibm_device_names if dev in qbraid_device_names]


inputs_qiskit_dw = [] if skip_remote_tests else ibm_devices()
circuits_qiskit_run = [cirq_circuit(), qiskit_circuit()]

### TESTS ###


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
@pytest.mark.parametrize("device_id", inputs_qiskit_dw)
def test_device_wrapper_ibm_from_api(device_id):
    """Test creating device wrapper from Qiskit device ID."""
    qbraid_device = device_wrapper(device_id)
    vendor_device = qbraid_device._device
    assert isinstance(qbraid_device, QiskitBackend)
    assert isinstance(vendor_device, IBMBackend)


def test_wrap_fake_provider():
    """Test wrapping fake Qiskit provider."""
    backend = FakeManilaV2()
    backend.simulator = True
    qbraid_device = QiskitBackend(backend)
    vendor_device = qbraid_device._device
    assert isinstance(qbraid_device, QiskitBackend)
    assert isinstance(vendor_device, Backend)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_queue_depth():
    """Test getting number of pending jobs for QiskitBackend."""
    ibm_device = device_wrapper("ibm_q_qasm_simulator")
    assert isinstance(ibm_device.queue_depth(), int)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
@pytest.mark.parametrize("circuit", circuits_qiskit_run)
def test_run_qiskit_device_wrapper(circuit):
    """Test run method from wrapped Qiskit backends"""
    qbraid_device = device_wrapper("ibm_q_qasm_simulator")
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, IBMJob)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_run_batch_qiskit_device_wrapper():
    """Test run_batch method from wrapped Qiskit backends"""
    qbraid_device = device_wrapper("ibm_q_qasm_simulator")
    qbraid_job = qbraid_device.run_batch(circuits_qiskit_run, shots=10)
    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, IBMJob)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_cancel_completed_batch_error():
    """Test that cancelling a batch job that has already reached its
    final state raises an error."""

    # Initialize your quantum device
    qbraid_device = device_wrapper("ibm_q_simulator_statevector")
    qbraid_job = qbraid_device.run_batch(circuits_qiskit_run, shots=10)

    # Initialize your timer
    timeout = 60  # Total time to wait for job to complete
    check_every = 2  # Check job status every 2 seconds
    elapsed_time = 0

    # Wait for job to complete, but not more than the timeout
    while elapsed_time < timeout:
        # Check if job has reached its final state
        status = qbraid_job.status()
        if QuantumJob.status_final(status):
            break

        # If not, sleep and then check again
        time.sleep(check_every)
        elapsed_time += check_every

    # If job hasn't finished even after waiting for the timeout period, cancel it
    if elapsed_time >= timeout:
        try:
            qbraid_job.cancel()
        except JobStateError:
            pass

    # Ensure that cancelling a finished job raises an error
    with pytest.raises(JobStateError):
        qbraid_job.cancel()

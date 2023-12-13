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
from qiskit.providers.basicaer.basicaerjob import BasicAerJob
from qiskit.providers.fake_provider import FakeManila, FakeProviderFactory
from qiskit_ibm_provider import IBMBackend, IBMJob

from qbraid import device_wrapper
from qbraid.providers import QuantumJob
from qbraid.providers.exceptions import JobStateError
from qbraid.providers.ibm import QiskitBackend, QiskitJob, QiskitProvider

from .fixtures import cirq_circuit, device_wrapper_inputs, qiskit_circuit

# Skip tests if IBM account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM storage)"


@pytest.fixture
def providers():
    """Return tuple of IBM and fake providers."""
    ibmq_token = os.getenv("QISKIT_IBM_TOKEN", None)
    qbraid_provider = QiskitProvider(qiskit_ibm_token=ibmq_token)
    ibm_provider = qbraid_provider._provider
    fake_provider = FakeProviderFactory().get_provider()
    return ibm_provider, fake_provider


def ibm_devices():
    """Get list of wrapped ibm backends for testing."""
    provider = QiskitProvider()
    backends = provider.get_devices(
        filters=lambda b: b.status().status_msg == "active", operational=True
    )
    qbraid_device_names = device_wrapper_inputs("IBM")
    ibm_device_names = [provider.ibm_to_qbraid_id(backend.name) for backend in backends]
    return [dev for dev in ibm_device_names if dev in qbraid_device_names]


def fake_ibm_devices():
    """Get list of fake wrapped ibm backends for testing"""
    fake_provider = FakeProviderFactory().get_provider()
    backends = fake_provider.backends()
    return [QiskitBackend(backend) for backend in backends if backend.configuration().n_qubits < 24]


inputs_qiskit_dw = [] if skip_remote_tests else ibm_devices()
circuits_qiskit_run = [cirq_circuit(), qiskit_circuit()]


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
    backend = FakeManila()
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


@pytest.mark.parametrize("qbraid_device", fake_ibm_devices())
@pytest.mark.parametrize("circuit", circuits_qiskit_run)
def test_run_fake_qiskit_device_wrapper(qbraid_device, circuit):
    """Test run method from wrapped fake Qiskit backends"""
    print(qbraid_device)
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, BasicAerJob)


@pytest.mark.parametrize("qbraid_device", fake_ibm_devices())
def test_run_fake_batch_qiskit_device_wrapper(qbraid_device):
    """Test run method from wrapped fake Qiskit backends"""
    qbraid_job = qbraid_device.run_batch(circuits_qiskit_run, shots=10)
    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, BasicAerJob)


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


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
@pytest.mark.parametrize("backend_name", ["ibmq_qasm_simulator", "fake_melbourne", "fake_almaden"])
def test_get_device_name_fake(providers, backend_name):  # pylint: disable=redefined-outer-name
    """Test edge cases for getting device name, e.g. .name, .name(), .backend_name"""
    provider, fake_provider = providers

    if backend_name.startswith("ibmq_"):
        backend = provider.get_backend(backend_name)
    else:
        backend = fake_provider.get_backend(backend_name)

    qbraid_device = QiskitBackend(backend)

    assert qbraid_device._get_device_name() == backend_name

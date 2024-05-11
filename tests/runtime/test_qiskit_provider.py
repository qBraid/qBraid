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
Unit tests for QiskitProvider class

"""
import os

import pytest
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import IBMBackend, QiskitRuntimeService, RuntimeJob

from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.qiskit import QiskitRuntimeProvider

# Skip tests if IBM account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM storage)"


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_ibm_provider():
    """Test getting IBMQ provider using qiskit_ibm_provider package."""
    provider = QiskitRuntimeProvider()
    assert isinstance(provider.runtime_service, QiskitRuntimeService)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_ibm_least_busy():
    """Test returning qbraid ID of least busy IBMQ QPU."""
    provider = QiskitRuntimeProvider()
    device = provider.least_busy()
    assert device.status().name == "ONLINE"
    assert isinstance(device._backend, IBMBackend)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_retrieving_ibm_job():
    """Test retrieving a previously submitted IBM job."""
    provider = QiskitRuntimeProvider()
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    qbraid_device = provider.get_device("ibmq_qasm_simulator")
    qbraid_job = qbraid_device.run(circuit, shots=1)
    ibm_job = qbraid_job._get_job()
    assert isinstance(ibm_job, RuntimeJob)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_retrieving_ibm_job_raises_error():
    """Test retrieving IBM job from unrecognized backend raises error."""
    provider = QiskitRuntimeProvider()
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    qbraid_device = provider.get_device("ibmq_qasm_simulator")
    qbraid_job = qbraid_device.run(circuit, shots=1)
    qbraid_job._job_id = "fake_id"
    with pytest.raises(QbraidRuntimeError):
        qbraid_job._get_job()


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_qiskit_runtime_provider():
    """Test getting QiskitRuntime provider."""
    provider = QiskitRuntimeProvider()
    service = provider.runtime_service
    assert isinstance(service, QiskitRuntimeService)

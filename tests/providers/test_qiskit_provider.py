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
Unit tests for QiskitProvider class

"""
import os
from unittest.mock import Mock

import pytest
from qiskit import QuantumCircuit
from qiskit_ibm_provider import IBMProvider
from qiskit_ibm_provider.job.ibm_circuit_job import IBMCircuitJob

from qbraid import device_wrapper
from qbraid.providers.exceptions import JobError
from qbraid.providers.ibm import QiskitProvider

# Skip tests if IBM account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM storage)"

backend_id_data = [
    ("ibm_nairobi", "ibm_q_nairobi"),
    ("ibmq_qasm_simulator", "ibm_q_qasm_simulator"),
    ("simulator_extended_stabilizer", "ibm_q_simulator_extended_stabilizer"),
]


@pytest.mark.parametrize("data", backend_id_data)
def test_get_qbraid_id(data):
    """Test converting backend name to qbraid_id."""
    original, expected = data
    result = QiskitProvider.ibm_to_qbraid_id(original)
    assert result == expected


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_ibm_provider():
    """Test getting IBMQ provider using qiskit_ibm_provider package."""
    ibmq_token = os.getenv("QISKIT_IBM_TOKEN", None)
    qbraid_provider = QiskitProvider(qiskit_ibm_token=ibmq_token)
    ibm_provider = qbraid_provider._provider
    assert isinstance(ibm_provider, IBMProvider)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_ibm_least_busy():
    """Test returning qbraid ID of least busy IBMQ QPU."""
    provider = QiskitProvider()
    qbraid_id = provider.ibm_least_busy_qpu()
    assert qbraid_id[:6] == "ibm_q_"


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_retrieving_ibm_job():
    """Test retrieving a previously submitted IBM job."""
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    qbraid_device = device_wrapper("ibm_q_qasm_simulator")
    qbraid_job = qbraid_device.run(circuit, shots=1)
    ibm_job = qbraid_job._get_job()
    assert isinstance(ibm_job, IBMCircuitJob)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_retrieving_ibm_job_raises_error():
    """Test retrieving IBM job from unrecognized backend raises error."""
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    qbraid_device = device_wrapper("ibm_q_qasm_simulator")
    qbraid_job = qbraid_device.run(circuit, shots=1)
    qbraid_job.device._device = Mock()
    with pytest.raises(JobError):
        qbraid_job._get_job()

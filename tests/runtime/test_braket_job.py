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
import pytest
from braket.circuits import Circuit
from braket.devices import LocalSimulator
from braket.tasks.quantum_task import QuantumTask as AwsQuantumTask

from qbraid.runtime.braket.job import BraketQuantumTask
from qbraid.runtime.braket import BraketDevice, BraketProvider, BraketQuantumTask


from unittest.mock import Mock, patch

from .fixtures import braket_circuit, cirq_circuit, device_wrapper_inputs, qiskit_circuit


skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of AWS storage)"
pytestmark = pytest.mark.skipif(skip_remote_tests, reason=REASON)

SV1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
DM1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/dm1"
HARMONY_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony"
LUCY_ARN = "arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy"

inputs_braket_run = [SV1_ARN]
inputs_braket_dw = [] if skip_remote_tests else device_wrapper_inputs("AWS")
circuits_braket_run = [braket_circuit(), cirq_circuit(meas=False), qiskit_circuit(meas=False)]

provider = BraketProvider()


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

@pytest.mark.parametrize("circuit", circuits_braket_run)
@pytest.mark.parametrize("device_id", inputs_braket_run)
def test_run_braket_device_wrapper(device_id, circuit):
    """Test run method of wrapped Braket devices"""
    qbraid_device = provider.get_device(device_id)
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job._task
    try:
        qbraid_job.cancel()
    except Exception:  # pylint: disable=broad-exception-caught
        pass
    assert isinstance(qbraid_job, BraketQuantumTask)
    assert isinstance(vendor_job, AwsQuantumTask)


def test_run_batch_braket_device_wrapper():
    """Test run_batch method of wrapped Braket devices"""
    qbraid_device = provider.get_device(SV1_ARN)
    qbraid_job_list = qbraid_device.run(circuits_braket_run, shots=10)
    qbraid_job = qbraid_job_list[0]
    for job in qbraid_job_list:
        try:
            job.cancel()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
    assert len(qbraid_job_list) == len(circuits_braket_run)
    assert isinstance(qbraid_job, BraketQuantumTask)
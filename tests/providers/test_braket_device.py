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
Unit tests for BraketDevice class

"""
import os

import pytest
from braket.aws import AwsDevice
from braket.tasks.quantum_task import QuantumTask as AwsQuantumTask
from qiskit import QuantumCircuit as QiskitCircuit

from qbraid import QbraidError, device_wrapper
from qbraid.interface import random_circuit
from qbraid.providers import QuantumJob
from qbraid.providers.aws import BraketDevice, BraketQuantumTask
from qbraid.providers.exceptions import ProgramValidationError

from .fixtures import braket_circuit, cirq_circuit, device_wrapper_inputs, qiskit_circuit

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of AWS storage)"
pytestmark = pytest.mark.skipif(skip_remote_tests, reason=REASON)

### FIXTURES ###

inputs_braket_dw = [] if skip_remote_tests else device_wrapper_inputs("AWS")

circuits_braket_run = [
    braket_circuit(),
    cirq_circuit(False),
    qiskit_circuit(False),
]  # circuits w/out measurement operation

inputs_braket_run = ["aws_sv_sim"]

### TESTS ###


def test_device_wrapper_id_error():
    """Test raising device wrapper error due to invalid device ID."""
    with pytest.raises(QbraidError):
        device_wrapper("Id123")


@pytest.mark.parametrize("device_id", inputs_braket_dw)
def test_device_wrapper_aws_from_api(device_id):
    """Test device wrapper for ids of devices available through Amazon Braket."""
    qbraid_device = device_wrapper(device_id)
    vendor_device = qbraid_device._device
    assert isinstance(qbraid_device, BraketDevice)
    assert isinstance(vendor_device, AwsDevice)


def test_device_wrapper_from_braket_arn():
    """Test creating device wrapper from Amazon Braket device ARN."""
    aws_device_arn = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
    qbraid_device = device_wrapper(aws_device_arn)
    vendor_device = qbraid_device._device
    assert isinstance(qbraid_device, BraketDevice)
    assert isinstance(vendor_device, AwsDevice)


def test_device_wrapper_properties():
    """Test extracting properties from BraketDevice"""
    device_id = "aws_oqc_lucy"
    wrapper = device_wrapper(device_id)
    assert wrapper.provider == "Oxford"
    assert wrapper.name == "Lucy"
    assert str(wrapper) == "AWS Oxford Lucy device wrapper"
    assert repr(wrapper) == "<BraketDevice(Oxford:'Lucy')>"


def test_queue_depth():
    """Test getting queue_depth BraketDevice"""
    aws_device = device_wrapper("aws_sv_sim")
    assert isinstance(aws_device.queue_depth(), int)


@pytest.mark.parametrize("circuit", circuits_braket_run)
@pytest.mark.parametrize("device_id", inputs_braket_run)
def test_run_braket_device_wrapper(device_id, circuit):
    """Test run method of wrapped Braket devices"""
    qbraid_device = device_wrapper(device_id)
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, BraketQuantumTask)
    assert isinstance(vendor_job, AwsQuantumTask)


def test_run_batch_braket_device_wrapper():
    """Test run_batch method of wrapped Braket devices"""
    qbraid_device = device_wrapper("aws_sv_sim")
    qbraid_job_list = qbraid_device.run_batch(circuits_braket_run, shots=10)
    qbraid_job = qbraid_job_list[0]
    assert len(qbraid_job_list) == len(circuits_braket_run)
    assert isinstance(qbraid_job, BraketQuantumTask)


def test_circuit_too_many_qubits():
    """Test that run method raises exception when input circuit
    num qubits exceeds that of wrapped AWS device."""
    device = device_wrapper("aws_ionq_harmony")
    num_qubits = device.num_qubits + 10
    circuit = QiskitCircuit(num_qubits)
    circuit.h([0, 1])
    circuit.cx(0, num_qubits - 1)
    with pytest.raises(ProgramValidationError):
        device.run(circuit)


def test_device_num_qubits():
    """Test device wrapper num qubits method"""
    five_qubit_device = device_wrapper("aws_ionq_harmony")
    assert five_qubit_device.num_qubits == 11


def test_wait_for_final_state():
    """Test function that returns after job is complete"""
    device = device_wrapper("aws_dm_sim")
    circuit = random_circuit("qiskit")
    job = device.run(circuit, shots=10)
    job.wait_for_final_state()
    status = job.status()
    assert QuantumJob.status_final(status)


def test_aws_device_available():
    """Test BraketDeviceWrapper avaliable output identical"""
    device = device_wrapper("aws_dm_sim")
    is_available_bool, is_available_time = device.is_available
    assert is_available_bool == device._device.is_available
    assert len(is_available_time.split(":")) == 3

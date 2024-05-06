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
from datetime import datetime

import pytest
from braket.aws.aws_device import AwsDevice
from braket.tasks.quantum_task import QuantumTask as AwsQuantumTask
from qiskit import QuantumCircuit as QiskitCircuit

from qbraid.interface import random_circuit
from qbraid.runtime import ResourceNotFoundError
from qbraid.runtime.aws import BraketDevice, BraketProvider, BraketQuantumTask
from qbraid.runtime.exceptions import ProgramValidationError

from .fixtures import braket_circuit, cirq_circuit, device_wrapper_inputs, qiskit_circuit

# Skip tests if IBM/AWS account auth/creds not configured
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
provider = None if skip_remote_tests else BraketProvider()


def test_device_wrapper_id_error():
    """Test raising device wrapper error due to invalid device ID."""
    with pytest.raises(ResourceNotFoundError):
        provider.get_device("Id123")


@pytest.mark.parametrize("device_id", inputs_braket_dw)
def test_device_wrapper_aws_from_api(device_id):
    """Test device wrapper for ids of devices available through Amazon Braket."""
    qbraid_device = provider.get_device(device_id)
    vendor_device = qbraid_device._device
    assert isinstance(qbraid_device, BraketDevice)
    assert isinstance(vendor_device, AwsDevice)


def test_device_wrapper_from_braket_arn():
    """Test creating device wrapper from Amazon Braket device ARN."""
    qbraid_device = provider.get_device(SV1_ARN)
    vendor_device = qbraid_device._device
    assert isinstance(qbraid_device, BraketDevice)
    assert isinstance(vendor_device, AwsDevice)


def test_device_wrapper_properties():
    """Test extracting properties from BraketDevice"""
    wrapper = provider.get_device(LUCY_ARN)
    assert str(wrapper) == "BraketDevice('Oxford Lucy')"
    assert repr(wrapper) == f"<qbraid.runtime.aws.device.BraketDevice('{LUCY_ARN}')>"


def test_queue_depth():
    """Test getting queue_depth BraketDevice"""
    aws_device = provider.get_device(SV1_ARN)
    assert isinstance(aws_device.queue_depth(), int)


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


def test_circuit_too_many_qubits():
    """Test that run method raises exception when input circuit
    num qubits exceeds that of wrapped AWS device."""
    device = provider.get_device(HARMONY_ARN)
    num_qubits = device.num_qubits + 10
    circuit = QiskitCircuit(num_qubits)
    circuit.h([0, 1])
    circuit.cx(0, num_qubits - 1)
    with pytest.raises(ProgramValidationError):
        device.run(circuit)


def test_device_num_qubits():
    """Test device wrapper num qubits method"""
    five_qubit_device = provider.get_device(HARMONY_ARN)
    assert five_qubit_device.num_qubits == 11


def test_wait_for_final_state():
    """Test function that returns after job is complete"""
    device = provider.get_device(DM1_ARN)
    circuit = random_circuit("qiskit")
    job = device.run(circuit, shots=10)
    job.wait_for_final_state()
    assert job.is_terminal_state()


def test_aws_device_available():
    """Test BraketDeviceWrapper avaliable output identical"""
    device = provider.get_device(DM1_ARN)
    is_available_bool, is_available_time, iso_str = device.availability_window()
    assert is_available_bool == device._device.is_available
    assert len(is_available_time.split(":")) == 3
    assert isinstance(iso_str, str)
    try:
        datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        pytest.fail("iso_str not in expected format")
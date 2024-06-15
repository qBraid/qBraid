# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for BraketProvider class

"""
import json
import warnings
from datetime import datetime, time
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from braket.aws.aws_session import AwsSession
from braket.aws.queue_information import QueueDepthInfo, QueueType
from braket.circuits import Circuit
from braket.device_schema import ExecutionDay
from braket.devices import Devices, LocalSimulator
from qiskit import QuantumCircuit as QiskitCircuit

from qbraid.interface import circuits_allclose
from qbraid.programs import ProgramSpec
from qbraid.runtime import (
    DeviceActionType,
    DeviceProgramTypeMismatchError,
    DeviceStatus,
    DeviceType,
    TargetProfile,
)
from qbraid.runtime.braket.availability import _calculate_future_time
from qbraid.runtime.braket.device import BraketDevice
from qbraid.runtime.braket.job import AmazonBraketVersionError, BraketQuantumTask
from qbraid.runtime.braket.provider import BraketProvider
from qbraid.runtime.braket.result import BraketGateModelJobResult
from qbraid.runtime.exceptions import JobStateError, ProgramValidationError

from ..fixtures.braket.gates import get_braket_gates

braket_gates = get_braket_gates()

SV1_ARN = Devices.Amazon.SV1


@pytest.fixture
def braket_provider():
    """Return a BraketProvider instance."""
    return BraketProvider()


@pytest.fixture
def sv1_profile():
    """Target profile for AWS SV1 device."""
    return TargetProfile(
        device_type=DeviceType.SIMULATOR,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
        action_type=DeviceActionType.OPENQASM,
    )


class TestAwsSession:
    """Test class for AWS session."""

    def __init__(self):
        self.region = "us-east-1"

    def get_device(self, arn):  # pylint: disable=unused-argument
        """Returns metadata for a device."""
        capabilities = {
            "action": {
                "braket.ir.openqasm.program": "literally anything",
                "paradigm": {"qubitCount": 2},
            }
        }
        cap_json = json.dumps(capabilities)
        metadata = {
            "deviceType": "SIMULATOR",
            "providerName": "Amazon Braket",
            "deviceCapabilities": cap_json,
        }

        return metadata


class ExecutionWindow:
    """Test class for execution window."""

    def __init__(self):
        self.windowStartHour = time(0)
        self.windowEndHour = time(23, 59, 59)
        self.executionDay = ExecutionDay.EVERYDAY


class Service:
    """Test class for braket device service."""

    def __init__(self):
        self.executionWindows = [ExecutionWindow()]


class TestProperties:
    """Test class for braket device properties."""

    def __init__(self):
        self.service = Service()


class TestAwsDevice:
    """Test class for braket device."""

    def __init__(self, arn, aws_session=None):
        self.arn = arn
        self.name = "SV1"
        self.aws_session = aws_session or TestAwsSession()
        self.status = "ONLINE"
        self.properties = TestProperties()
        self.is_available = True

    @staticmethod
    def get_device_region(arn):  # pylint: disable=unused-argument
        """Returns the region of a device."""
        return "us-east-1"


def test_device_wrapper_id_error(braket_provider):
    """Test raising device wrapper error due to invalid device ID."""
    with pytest.raises(ValueError):
        braket_provider.get_device("Id123")


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_device_profile_attributes(mock_aws_device, sv1_profile):
    """Test that device profile attributes are correctly set."""
    mock_aws_device.return_value = Mock()
    device = BraketDevice(sv1_profile)
    assert device.id == sv1_profile.get("device_id")
    assert device.num_qubits == sv1_profile.get("num_qubits")
    assert device._target_spec == sv1_profile.get("program_spec")
    assert device.device_type == DeviceType(sv1_profile.get("device_type"))
    assert device.profile.get("action_type") == "OPENQASM"


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_queue_depth(mock_aws_device, sv1_profile):
    """Test getting queue_depth BraketDevice"""
    mock_aws_device.queue_depth.return_value = QueueDepthInfo(
        quantum_tasks={QueueType.NORMAL: "19", QueueType.PRIORITY: "3"},
        jobs="0 (3 prioritized job(s) running)",
    )
    device = BraketDevice(sv1_profile)
    queue_depth = device.queue_depth()
    assert isinstance(queue_depth, int)


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_circuit_too_many_qubits(mock_aws_device, sv1_profile):
    """Test that run method raises exception when input circuit
    num qubits exceeds that of wrapped AWS device."""
    mock_aws_device.return_value = Mock()
    device = BraketDevice(sv1_profile)
    num_qubits = device.num_qubits + 10
    circuit = QiskitCircuit(num_qubits)
    circuit.h([0, 1])
    circuit.cx(0, num_qubits - 1)
    with pytest.raises(ProgramValidationError):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            device.run(circuit)


def test_aws_device_available(braket_provider):
    """Test BraketDeviceWrapper avaliable output identical"""
    with (
        patch("qbraid.runtime.braket.provider.AwsDevice") as mock_aws_device,
        patch("qbraid.runtime.braket.device.AwsDevice") as mock_aws_device_2,
    ):
        mock_device = TestAwsDevice(SV1_ARN)
        mock_device.is_available = False
        mock_aws_device.return_value = mock_device
        mock_aws_device_2.return_value = mock_device
        device = braket_provider.get_device(SV1_ARN)
        _, is_available_time, iso_str = device.availability_window()
        assert len(is_available_time.split(":")) == 3
        assert isinstance(iso_str, str)
        try:
            datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pytest.fail("iso_str not in expected format")


def test_get_aws_session():
    """Test getting an AWS session."""
    with patch("boto3.session.Session") as mock_boto_session:
        mock_boto_session.aws_access_key_id.return_value = "aws_access_key_id"
        mock_boto_session.aws_secret_access_key.return_value = "aws_secret_access_key"
        aws_session = BraketProvider()._get_aws_session()
        assert aws_session.boto_session.region_name == "us-east-1"
        assert isinstance(aws_session, AwsSession)


def test_build_runtime_profile():
    """Test building a runtime profile."""
    provider = BraketProvider()
    device = TestAwsDevice(SV1_ARN)
    profile = provider._build_runtime_profile(device=device, extra="data")
    assert profile.get("device_type") == DeviceType.SIMULATOR.name
    assert profile.get("provider_name") == "Amazon Braket"
    assert profile.get("device_id") == SV1_ARN
    assert profile.get("extra") == "data"


def test_get_device():
    """Test getting a Braket device."""
    provider = BraketProvider()
    with (
        patch("qbraid.runtime.braket.provider.AwsDevice") as mock_aws_device,
        patch("qbraid.runtime.braket.device.AwsDevice") as mock_aws_device_2,
    ):
        mock_aws_device.return_value = TestAwsDevice(SV1_ARN)
        mock_aws_device_2.return_value = TestAwsDevice(SV1_ARN)
        device = provider.get_device(SV1_ARN)
        assert device.id == SV1_ARN
        assert device.name == "SV1"
        assert str(device) == "BraketDevice('Amazon Braket SV1')"
        assert device.status() == DeviceStatus.ONLINE
        assert isinstance(device, BraketDevice)


@patch("qbraid.runtime.braket.job.AwsQuantumTask")
def test_load_completed_job(mock_aws_quantum_task):
    """Test is terminal state method for BraketQuantumTask."""
    circuit = Circuit().h(0).cnot(0, 1)
    mock_device = LocalSimulator()
    mock_job = mock_device.run(circuit, shots=10)
    mock_aws_quantum_task.return_value = mock_job
    job = BraketQuantumTask(mock_job.id)
    assert job.metadata()["job_id"] == mock_job.id
    assert job.is_terminal_state()


@patch("qbraid.runtime.braket.BraketProvider")
def test_is_available(mock_provider):
    """Test device availability function."""
    provider = mock_provider.return_value

    mock_device_0 = Mock()
    mock_device_0.availability_window.return_value = (True, 0, 0)
    mock_device_0._device.is_available = True

    mock_device_1 = Mock()
    mock_device_1.availability_window.return_value = (False, 0, 0)
    mock_device_1._device.is_available = False

    provider.get_devices.return_value = [mock_device_0, mock_device_1]

    devices = provider.get_devices()
    for device in devices:
        is_available_bool, _, _ = device.availability_window()
        assert device._device.is_available == is_available_bool


@patch("qbraid.runtime.braket.BraketProvider")
def test_get_quantum_tasks_by_tag(mock_provider):
    """Test getting tagged quantum tasks."""
    provider = mock_provider.return_value
    provider.REGIONS = ["us-east-1", "us-west-1"]
    provider._get_default_region.return_value = "us-east-1"
    alt_regions = ["us-west-1"]

    mock_device = Mock()
    provider.get_device.return_value = mock_device

    mock_task_1 = Mock()
    mock_task_1.id = "task1"

    mock_task_2 = Mock()
    mock_task_2.id = "task2"

    circuit = Circuit().h(0).cnot(0, 1)
    mock_device.run.side_effect = [mock_task_1, mock_task_2]

    key, value1, value2 = "abc123", "val1", "val2"
    mock_task_1.tags = {key: value1}
    mock_task_2.tags = {key: value2}
    provider.get_tasks_by_tag.side_effect = [
        [mock_task_1.id, mock_task_2.id],
        [mock_task_1.id],
        [],
    ]

    task1 = mock_device.run(circuit, shots=2, tags={key: value1})
    task2 = mock_device.run(circuit, shots=2, tags={key: value2})

    assert set([task1.id, task2.id]) == set(provider.get_tasks_by_tag(key))
    assert len(provider.get_tasks_by_tag(key, values=[value1], region_names=["us-east-1"])) == 1
    assert len(provider.get_tasks_by_tag(key, region_names=alt_regions)) == 0


def test_braket_queue_visibility():
    """Test methods that check Braket device/job queue."""
    with patch("qbraid.runtime.braket.BraketProvider") as _:
        circuit = Circuit().h(0).cnot(0, 1)

        mock_device = Mock()
        mock_job = Mock()
        mock_job.queue_position.return_value = 5  # job is 5th in queue

        mock_device.run.return_value = mock_job

        device = mock_device
        job = device.run(circuit, shots=10)
        queue_position = job.queue_position()
        job.cancel()
        assert isinstance(queue_position, int)


@pytest.mark.parametrize(
    "available_time, expected",
    [
        (3600, "2024-01-01T01:00:00Z"),
        (1800, "2024-01-01T00:30:00Z"),
        (45, "2024-01-01T00:00:45Z"),
    ],
)
def test_future_utc_datetime(available_time, expected):
    """Test calculating future utc datetime"""
    current_utc_datime = datetime(2024, 1, 1, 0, 0, 0)
    _, datetime_str = _calculate_future_time(available_time, current_utc_datime)
    assert datetime_str == expected


@pytest.mark.parametrize("position,expected", [(10, 10), (">2000", 2000)])
@patch("qbraid.runtime.braket.job.AwsQuantumTask")
def test_queue_position(mock_aws_quantum_task, position, expected):
    """Test getting queue_depth BraketDevice"""
    mock_queue_position_return = MagicMock()
    mock_queue_position_return.queue_position = position
    mock_aws_quantum_task.return_value.queue_position.return_value = mock_queue_position_return
    job = BraketQuantumTask("job_id")
    assert job.queue_position() == expected


@patch("qbraid.runtime.braket.job.AwsQuantumTask")
def test_queue_position_raises_version_error(mock_aws_quantum_task):
    """Test handling of AttributeError leads to raising AmazonBraketVersionError."""
    mock_aws_quantum_task.return_value.queue_position.side_effect = AttributeError
    job = BraketQuantumTask("job_id")
    with pytest.raises(AmazonBraketVersionError) as excinfo:
        job.queue_position()
    assert "Queue visibility is only available for amazon-braket-sdk>=1.56.0" in str(excinfo.value)


def test_aquila_job_raise_for_cancel_terminal():
    """Test raising an error when trying to cancel a completed/failed job."""
    with patch("qbraid.runtime.job.QuantumJob.is_terminal_state", return_value=True):
        job = BraketQuantumTask(SV1_ARN, task=Mock())
        with pytest.raises(JobStateError):
            job.cancel()


def test_measurements():
    """Test measurements method of BraketGateModelJobResult class."""
    mock_measurements = np.array([[0, 1, 1], [1, 0, 1]])
    mock_result = MagicMock()
    mock_result.measurements = mock_measurements
    result = BraketGateModelJobResult(mock_result)
    expected_output = np.array([[1, 1, 0], [1, 0, 1]])
    np.testing.assert_array_equal(result.measurements(), expected_output)


def test_raw_counts():
    """Test raw_counts method of BraketGateModelJobResult class."""
    mock_measurement_counts = {(0, 1, 1): 10, (1, 0, 1): 5}
    mock_result = MagicMock()
    mock_result.measurement_counts = mock_measurement_counts
    result = BraketGateModelJobResult(mock_result)
    expected_output = {"110": 10, "101": 5}
    assert result.raw_counts() == expected_output


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_transform_circuit_sv1(mock_aws_device, sv1_profile):
    """Test transform method for device with OpenQASM action type."""
    mock_aws_device.return_value = Mock()
    device = BraketDevice(sv1_profile)
    circuit = Circuit().h(0).cnot(0, 2)
    transformed_expected = Circuit().h(0).cnot(0, 1)
    transformed_circuit = device.transform(circuit)
    assert transformed_circuit == transformed_expected


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_transform_raises_for_mismatch(mock_aws_device, braket_circuit):
    """Test raising exception for mismatched action type AHS and program type circuit."""
    mock_aws_device.return_value = Mock()
    profile = TargetProfile(
        device_type=DeviceType.SIMULATOR,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
        action_type=DeviceActionType.AHS,
    )
    device = BraketDevice(profile)
    with pytest.raises(DeviceProgramTypeMismatchError):
        device.transform(braket_circuit)


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_braket_ionq_transform(mock_aws_device):
    """Test converting Amazon Braket circuit to use only IonQ supprted gates"""
    mock_aws_device.return_value = Mock()
    profile = TargetProfile(
        device_type=DeviceType.QPU,
        num_qubits=11,
        program_spec=ProgramSpec(Circuit),
        provider_name="IonQ",
        device_id="arn:aws:braket:us-east-1::device/qpu/ionq/Harmony",
        action_type=DeviceActionType.OPENQASM,
    )
    device = BraketDevice(profile)

    toffoli_circuit = Circuit().ccnot(0, 1, 2)
    transformed_circuit = device.transform(toffoli_circuit)
    assert isinstance(transformed_circuit, Circuit)
    assert toffoli_circuit.depth == 1
    assert transformed_circuit.depth == 11
    assert circuits_allclose(transformed_circuit, toffoli_circuit)

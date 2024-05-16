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
Unit tests for BraketProvider class

"""
import json
import os
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import Mock, patch

import numpy as np
import pytest
from braket.aws.aws_device import AwsDevice
from braket.aws.aws_session import AwsSession
from braket.aws.queue_information import QueueDepthInfo, QueueType
from braket.circuits import Circuit
from braket.device_schema import ExecutionDay
from braket.devices import LocalSimulator
from braket.tracking import Tracker
from qiskit import QuantumCircuit as QiskitCircuit

from qbraid.programs import ProgramSpec
from qbraid.runtime import DeviceType, TargetProfile
from qbraid.runtime.braket import BraketDevice, BraketProvider, BraketQuantumTask
from qbraid.runtime.braket.device import _future_utc_datetime
from qbraid.runtime.braket.tracker import get_quantum_task_cost
from qbraid.runtime.exceptions import JobStateError, ProgramValidationError

SV1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"

# Skip tests if AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of AWS storage)"

# pylint: disable=redefined-outer-name


@pytest.fixture
def braket_circuit():
    """Returns low-depth, one-qubit Braket circuit to be used for testing."""
    circuit = Circuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
    yield circuit


@pytest.fixture
def aws_session():
    """Return AWS session."""
    provider = BraketProvider()
    yield provider._get_aws_session()


@pytest.fixture
def braket_provider():
    """Return a BraketProvider instance."""
    yield BraketProvider()


@pytest.fixture
def braket_most_busy():
    """Return the most busy device for testing purposes."""
    provider = BraketProvider()
    qbraid_devices = provider.get_devices(
        types=["QPU"], statuses=["ONLINE"], provider_names=["Rigetti", "IonQ", "Oxford"]
    )

    qbraid_device = None
    max_queued = 0
    for device in qbraid_devices:
        jobs_queued = device.queue_depth()
        if jobs_queued is not None and jobs_queued > max_queued:
            max_queued = jobs_queued
            qbraid_device = device
    yield qbraid_device


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
def test_device_profile_attributes(mock_aws_device):
    """Test that device profile attributes are correctly set."""
    mock_aws_device.return_value = Mock()
    profile = TargetProfile(
        device_type=DeviceType.SIMULATOR,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
    )
    device = BraketDevice(profile)
    assert device.id == profile.get("device_id")
    assert device.num_qubits == profile.get("num_qubits")
    assert device._target_spec == profile.get("program_spec")
    assert device.device_type == DeviceType(profile.get("device_type"))


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_queue_depth(mock_aws_device):
    """Test getting queue_depth BraketDevice"""
    mock_aws_device.queue_depth.return_value = QueueDepthInfo(
        quantum_tasks={QueueType.NORMAL: "19", QueueType.PRIORITY: "3"},
        jobs="0 (3 prioritized job(s) running)",
    )
    profile = TargetProfile(
        device_type=DeviceType.SIMULATOR,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
    )
    device = BraketDevice(profile)
    queue_depth = device.queue_depth()
    assert isinstance(queue_depth, int)


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_circuit_too_many_qubits(mock_aws_device):
    """Test that run method raises exception when input circuit
    num qubits exceeds that of wrapped AWS device."""
    mock_aws_device.return_value = Mock()
    profile = TargetProfile(
        device_type=DeviceType.SIMULATOR,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
    )
    device = BraketDevice(profile)
    num_qubits = device.num_qubits + 10
    circuit = QiskitCircuit(num_qubits)
    circuit.h([0, 1])
    circuit.cx(0, num_qubits - 1)
    with pytest.raises(ProgramValidationError):
        device.run(circuit)


def test_aws_device_available(braket_provider):
    """Test BraketDeviceWrapper avaliable output identical"""
    with (
        patch("qbraid.runtime.braket.provider.AwsDevice") as mock_aws_device,
        patch("qbraid.runtime.braket.device.AwsDevice") as mock_aws_device_2,
    ):
        mock_aws_device.return_value = TestAwsDevice(SV1_ARN)
        mock_aws_device_2.return_value = TestAwsDevice(SV1_ARN)
        device = braket_provider.get_device(SV1_ARN)
        is_available_bool, is_available_time, iso_str = device.availability_window()
        assert is_available_bool == device._device.is_available
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
    profile = provider._build_runtime_profile(device=device)
    assert profile.get("device_type") == DeviceType.SIMULATOR
    assert profile.get("provider_name") == "Amazon Braket"
    assert profile.get("device_id") == SV1_ARN


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


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_quantum_task_cost_simulator():
    """Test getting cost of quantum task run on an AWS simulator."""
    provider = BraketProvider()
    device = provider.get_device("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
    circuit = Circuit().h(0).cnot(0, 1)

    with Tracker() as tracker:
        task = device.run(circuit, shots=2)
        task.result()

    expected = tracker.simulator_tasks_cost()
    calculated = get_quantum_task_cost(task.id, provider._get_aws_session())
    assert expected == calculated


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_quantum_task_cost_cancelled(braket_most_busy, braket_circuit):
    """Test getting cost of quantum task that was cancelled."""
    if braket_most_busy is None:
        pytest.skip("No AWS QPU devices available")

    provider = BraketProvider()

    # AwsSession region must match device region
    region_name = AwsDevice.get_device_region(braket_most_busy.id)
    aws_session = provider._get_aws_session(region_name)

    qbraid_job = braket_most_busy.run(braket_circuit, shots=10)
    qbraid_job.cancel()

    task_arn = qbraid_job.id

    try:
        qbraid_job.wait_for_final_state(timeout=30)
        final_state_reached = True
    except JobStateError:
        final_state_reached = False

    # Based on whether final state was reached or not, proceed to verify expected outcomes
    if final_state_reached:
        # Verify cost is as expected when job reaches a final state
        cost = get_quantum_task_cost(task_arn, aws_session)
        assert cost == Decimal(0), f"Expected cost to be 0 when job is in a final state, got {cost}"
    else:
        # Verify the appropriate error is raised when job has not reached a final state
        with pytest.raises(ValueError) as exc_info:
            get_quantum_task_cost(task_arn, aws_session)

        expected_msg_partial = f"Task {task_arn} is not COMPLETED."
        assert expected_msg_partial in str(
            exc_info.value
        ), "Unexpected error message for non-final job state"


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_quantum_task_cost_region_mismatch(braket_most_busy, braket_circuit):
    """Test getting cost of quantum task raises value error on region mismatch."""
    if braket_most_busy is None:
        pytest.skip("No AWS QPU devices available")

    braket_device = braket_most_busy._device
    task = braket_device.run(braket_circuit, shots=10)
    task.cancel()

    task_arn = task.id
    task_region = task_arn.split(":")[3]
    other_region = "eu-west-2" if task_region == "us-east-1" else "us-east-1"

    provider = BraketProvider()
    aws_session = provider._get_aws_session(other_region)

    with pytest.raises(ValueError) as excinfo:
        get_quantum_task_cost(task_arn, aws_session)

    assert (
        str(excinfo.value)
        == f"AwsSession region {other_region} does not match task region {task_region}"
    )


@pytest.mark.parametrize(
    "hours, minutes, seconds, expected",
    [
        (1, 0, 0, "2024-01-01T01:00:00Z"),
        (0, 30, 0, "2024-01-01T00:30:00Z"),
        (0, 0, 45, "2024-01-01T00:00:45Z"),
    ],
)
def test_future_utc_datetime(hours, minutes, seconds, expected):
    """Test calculating future utc datetime"""
    with patch("qbraid.runtime.braket.device.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 0, 0, 0)
        assert _future_utc_datetime(hours, minutes, seconds) == expected

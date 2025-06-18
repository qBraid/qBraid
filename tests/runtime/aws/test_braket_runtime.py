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
import datetime
import importlib.util
import json
import warnings
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from botocore.exceptions import NoCredentialsError
from braket.aws.aws_session import AwsSession
from braket.aws.queue_information import QueueDepthInfo, QueueType
from braket.circuits import Circuit
from braket.device_schema import ExecutionDay
from braket.devices import Devices, LocalSimulator

from qbraid.exceptions import QbraidError
from qbraid.interface import circuits_allclose
from qbraid.programs import ExperimentType, ProgramSpec, load_program
from qbraid.runtime import (
    DeviceProgramTypeMismatchError,
    DeviceStatus,
    GateModelResultData,
    TargetProfile,
)
from qbraid.runtime.aws.availability import _calculate_future_time
from qbraid.runtime.aws.device import BraketDevice
from qbraid.runtime.aws.job import AmazonBraketVersionError, BraketQuantumTask
from qbraid.runtime.aws.provider import BraketProvider
from qbraid.runtime.aws.result_builder import BraketGateModelResultBuilder
from qbraid.runtime.exceptions import JobStateError, ProgramValidationError

from ...fixtures.braket.gates import get_braket_gates

braket_gates = get_braket_gates()

pytket_not_installed = importlib.util.find_spec("pytket") is None

SV1_ARN = Devices.Amazon.SV1


@pytest.fixture
def braket_provider():
    """Return a BraketProvider instance."""
    return BraketProvider()


@pytest.fixture
def sv1_profile():
    """Target profile for AWS SV1 device."""
    return TargetProfile(
        simulator=True,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
        experiment_type=ExperimentType.GATE_MODEL,
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
            },
            "paradigm": {
                "qubitCount": 2,
                "nativeGateSet": ["gate1", "gate2"],
            },
        }
        cap_json = json.dumps(capabilities)
        metadata = {
            "deviceType": "SIMULATOR",
            "providerName": "Amazon Braket",
            "deviceCapabilities": cap_json,
        }

        return metadata

    def cancel_quantum_task(self, arn):  # pylint: disable=unused-argument
        """Cancel a quantum task."""
        return None


class ExecutionWindow:
    """Test class for execution window."""

    def __init__(self):
        self.windowStartHour = datetime.time(0)
        self.windowEndHour = datetime.time(23, 59, 59)
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


class MockTask:
    """Mock task class."""

    def __init__(self, arg):
        self.id = arg
        self.arn = arg
        self._aws_session = TestAwsSession()

    def result(self):
        """Mock result method."""
        return "not a result"

    def state(self):
        """Mock state method."""
        return "COMPLETED" if self.id == "task1" else "RUNNING"

    def cancel(self):
        """Mock cancel method."""
        raise RuntimeError

    def metadata(self):
        """Mock metadata method."""
        return {"status": self.state(), "quantumTaskArn": self.id, "deviceArn": SV1_ARN}


@pytest.fixture
def mock_sv1():
    """Return a mock SV1 device."""
    return TestAwsDevice(SV1_ARN)


@pytest.fixture
def mock_aws_configure():
    """Mock aws_conifugre function."""
    with patch("qbraid.runtime.aws.provider.aws_configure") as mock:
        yield mock


@pytest.mark.parametrize(
    "input_keys, expected_calls",
    [
        (
            {"aws_access_key_id": "AKIA...", "aws_secret_access_key": "secret"},
            {"aws_access_key_id": "AKIA...", "aws_secret_access_key": "secret"},
        ),
        ({}, {"aws_access_key_id": "default_key", "aws_secret_access_key": "default_secret"}),
        (
            {"aws_access_key_id": "AKIA..."},
            {"aws_access_key_id": "AKIA...", "aws_secret_access_key": "default_secret"},
        ),
    ],
)
def test_save_config(mock_aws_configure, input_keys, expected_calls):
    """Test save_config method of BraketProvider class."""
    instance = BraketProvider()
    instance.aws_access_key_id = "default_key"
    instance.aws_secret_access_key = "default_secret"

    instance.save_config(**input_keys)

    mock_aws_configure.assert_called_once_with(**expected_calls)


def test_provider_get_aws_session():
    """Test getting an AWS session."""
    with patch("boto3.session.Session") as mock_boto_session:
        mock_boto_session.aws_access_key_id.return_value = "aws_access_key_id"
        mock_boto_session.aws_secret_access_key.return_value = "aws_secret_access_key"
        aws_session = BraketProvider()._get_aws_session()
        assert aws_session.boto_session.region_name == "us-east-1"
        assert isinstance(aws_session, AwsSession)


def test_provider_get_aws_session_with_session_token():
    """Test getting an AWS session with session token."""
    with patch("boto3.session.Session") as mock_boto_session:
        mock_boto_session.aws_access_key_id.return_value = "aws_access_key_id"
        mock_boto_session.aws_secret_access_key.return_value = "aws_secret_access_key"
        mock_boto_session.get_credentials.return_value.token = "session_token"
        aws_session = BraketProvider(aws_session_token="session_token")._get_aws_session()
        assert aws_session.boto_session.region_name == "us-east-1"
        assert isinstance(aws_session, AwsSession)
        assert aws_session.boto_session.get_credentials().token == "session_token"


def test_provider_get_devices_raises(braket_provider):
    """Test raising device wrapper error due to invalid device ID."""
    with pytest.raises(ValueError):
        braket_provider.get_device("Id123")


def test_provider_build_runtime_profile(mock_sv1):
    """Test building a runtime profile."""
    provider = BraketProvider()
    profile = provider._build_runtime_profile(device=mock_sv1, extra="data")
    assert profile.get("simulator") is True
    assert profile.get("provider_name") == "Amazon Braket"
    assert profile.get("device_id") == SV1_ARN
    assert profile.get("extra") == "data"
    assert profile.get("basis_gates") == {"gate1", "gate2"}


@pytest.mark.parametrize(
    "region_names, key, values, expected",
    [(["us-west-1"], "Project", ["X"], ["arn:aws:resource1", "arn:aws:resource2"])],
)
@patch("boto3.client")
def test_provider_get_tasks_by_tag(mock_boto_client, region_names, key, values, expected):
    """Test fetching tagged resources from AWS."""
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client
    mock_client.get_resources.return_value = {
        "ResourceTagMappingList": [
            {"ResourceARN": "arn:aws:resource1"},
            {"ResourceARN": "arn:aws:resource2"},
        ]
    }

    provider = BraketProvider()
    result = provider.get_tasks_by_tag(key, values, region_names)

    # Assert the results
    mock_boto_client.assert_called_with("resourcegroupstaggingapi", region_name="us-west-1")
    mock_client.get_resources.assert_called_once_with(TagFilters=[{"Key": key, "Values": values}])
    assert result == expected


def test_provider_get_device(mock_sv1):
    """Test getting a Braket device."""
    provider = BraketProvider()
    with (
        patch("qbraid.runtime.aws.provider.AwsDevice") as mock_aws_device,
        patch("qbraid.runtime.aws.device.AwsDevice") as mock_aws_device_2,
    ):
        mock_aws_device.return_value = mock_sv1
        mock_aws_device_2.return_value = mock_sv1
        device = provider.get_device(SV1_ARN)
        assert device.id == SV1_ARN
        assert device.name == "SV1"
        assert str(device) == "BraketDevice('Amazon Braket SV1')"
        assert device.status() == DeviceStatus.ONLINE
        assert isinstance(device, BraketDevice)


def test_provider_get_devices(mock_sv1):
    """Test getting list of Braket devices."""
    with (
        patch("qbraid.runtime.aws.provider.AwsDevice.get_devices", return_value=[mock_sv1]),
        patch("qbraid.runtime.aws.device.AwsDevice") as mock_aws_device_2,
    ):
        provider = BraketProvider()
        mock_aws_device_2.return_value = mock_sv1
        devices = provider.get_devices()
        assert len(devices) == 1
        assert devices[0].id == SV1_ARN


@patch("qbraid.runtime.aws.device.AwsDevice")
def test_device_profile_attributes(mock_aws_device, sv1_profile):
    """Test that device profile attributes are correctly set."""
    mock_aws_device.return_value = Mock()
    device = BraketDevice(sv1_profile)
    assert device.id == sv1_profile.get("device_id")
    assert device.num_qubits == sv1_profile.get("num_qubits")
    assert device._target_spec == sv1_profile.get("program_spec")
    assert device.simulator == sv1_profile.get("simulator")
    assert device.profile.get("experiment_type").value == "gate_model"


@patch("qbraid.runtime.aws.device.AwsDevice")
def test_device_queue_depth(mock_aws_device, sv1_profile):
    """Test getting queue_depth BraketDevice"""
    mock_aws_device.queue_depth.return_value = QueueDepthInfo(
        quantum_tasks={QueueType.NORMAL: "19", QueueType.PRIORITY: "3"},
        jobs="0 (3 prioritized job(s) running)",
    )
    device = BraketDevice(sv1_profile)
    queue_depth = device.queue_depth()
    assert isinstance(queue_depth, int)


@patch("qbraid.runtime.aws.device.AwsDevice")
def test_device_run_circuit_too_many_qubits(mock_aws_device, sv1_profile):
    """Test that run method raises exception when input circuit
    num qubits exceeds that of wrapped AWS device."""
    mock_aws_device.return_value = Mock()
    device = BraketDevice(sv1_profile)
    circuit = Circuit().h(0).cnot(0, device.num_qubits + 1)
    program = load_program(circuit)
    program.populate_idle_qubits()
    run_input = program.program
    with pytest.raises(ProgramValidationError):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            device.run(run_input)


@patch("qbraid.runtime.aws.device.AwsDevice")
def test_batch_run(mock_aws_device, sv1_profile):
    """Test batch run method of BraketDevice."""
    mock_aws_device.return_value = MagicMock()
    mock_aws_device.return_value.__iter__.return_value = [MockTask("task1"), MockTask("task2")]
    mock_aws_device.return_value.status = "ONLINE"
    device = BraketDevice(sv1_profile)
    circuits = [Circuit().h(0).cnot(0, 1), Circuit().h(0).cnot(0, 1)]
    tasks = device.run(circuits, shots=10)
    assert isinstance(tasks, list)


@pytest.mark.parametrize(
    "available_time, expected",
    [
        (3600, "2024-01-01T01:00:00Z"),
        (1800, "2024-01-01T00:30:00Z"),
        (45, "2024-01-01T00:00:45Z"),
    ],
)
def test_availability_future_utc_datetime(available_time, expected):
    """Test calculating future utc datetime"""
    current_utc_datime = datetime.datetime(2024, 1, 1, 0, 0, 0)
    _, datetime_str = _calculate_future_time(available_time, current_utc_datime)
    assert datetime_str == expected


def test_device_availability_window(braket_provider, mock_sv1):
    """Test BraketDeviceWrapper avaliable output identical"""
    with (
        patch("qbraid.runtime.aws.provider.AwsDevice") as mock_aws_device,
        patch("qbraid.runtime.aws.device.AwsDevice") as mock_aws_device_2,
    ):
        mock_device = mock_sv1
        mock_device.is_available = False
        mock_aws_device.return_value = mock_device
        mock_aws_device_2.return_value = mock_device
        device = braket_provider.get_device(SV1_ARN)
        _, is_available_time, iso_str = device.availability_window()
        assert len(is_available_time.split(":")) == 3
        assert isinstance(iso_str, str)
        try:
            datetime.datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pytest.fail("iso_str not in expected format")


@patch("qbraid.runtime.aws.BraketProvider")
def test_device_is_available(mock_provider):
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


@patch("qbraid.runtime.aws.device.AwsDevice")
def test_device_transform_circuit_sv1(mock_aws_device, sv1_profile):
    """Test transform method for device with OpenQASM action type."""
    mock_aws_device.return_value = Mock()
    device = BraketDevice(sv1_profile)
    circuit = Circuit().h(0).cnot(0, 2)
    transformed_expected = Circuit().h(0).cnot(0, 1)
    transformed_circuit = device.transform(circuit)
    assert transformed_circuit == transformed_expected


@patch("qbraid.runtime.aws.device.AwsDevice")
def test_device_transform_raises_for_mismatch(mock_aws_device, braket_circuit):
    """Test raising exception for mismatched action type AHS and program type circuit."""
    mock_aws_device.return_value = Mock()
    profile = TargetProfile(
        simulator=True,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
        experiment_type=ExperimentType.AHS,
    )
    device = BraketDevice(profile)
    with pytest.raises(DeviceProgramTypeMismatchError):
        device.transform(braket_circuit)


@pytest.mark.skipif(pytket_not_installed, reason="pytket not installed")
@patch("qbraid.runtime.aws.device.AwsDevice")
def test_device_ionq_transform(mock_aws_device):
    """Test converting Amazon Braket circuit to use only IonQ supprted gates"""
    mock_aws_device.return_value = Mock()
    profile = TargetProfile(
        simulator=False,
        num_qubits=11,
        program_spec=ProgramSpec(Circuit),
        provider_name="IonQ",
        device_id="arn:aws:braket:us-east-1::device/qpu/ionq/Harmony",
        experiment_type=ExperimentType.GATE_MODEL,
    )
    device = BraketDevice(profile)

    toffoli_circuit = Circuit().ccnot(0, 1, 2)
    transformed_circuit = device.transform(toffoli_circuit)
    assert isinstance(transformed_circuit, Circuit)
    assert toffoli_circuit.depth == 1
    assert transformed_circuit.depth == 11
    assert circuits_allclose(transformed_circuit, toffoli_circuit)


@patch("qbraid.runtime.aws.BraketProvider")
def test_device_submit_task_with_tags(mock_provider):
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


@patch("qbraid.runtime.aws.job.AwsQuantumTask")
def test_job_load_completed(mock_aws_quantum_task):
    """Test is terminal state method for BraketQuantumTask."""
    circuit = Circuit().h(0).cnot(0, 1)
    mock_device = LocalSimulator()
    mock_job = mock_device.run(circuit, shots=10)
    mock_job.metadata = lambda: {
        "status": mock_job.state(),
        "quantumTaskArn": mock_job.id,
        "deviceArn": mock_device.name,
    }
    mock_aws_quantum_task.return_value = mock_job
    job = BraketQuantumTask(mock_job.id)
    assert job.metadata()["job_id"] == mock_job.id
    assert job.is_terminal_state()
    res = job.result()
    data: GateModelResultData = res.data
    assert data.measurements is not None


@pytest.mark.parametrize("position,expected", [(10, 10), (">2000", 2000)])
@patch("qbraid.runtime.aws.job.AwsQuantumTask")
def test_job_queue_position(mock_aws_quantum_task, position, expected):
    """Test getting queue_depth BraketDevice"""
    mock_queue_position_return = MagicMock()
    mock_queue_position_return.queue_position = position
    mock_aws_quantum_task.return_value.queue_position.return_value = mock_queue_position_return
    job = BraketQuantumTask("job_id")
    assert job.queue_position() == expected


@patch("qbraid.runtime.aws.job.AwsQuantumTask")
def test_job_queue_position_raises_version_error(mock_aws_quantum_task):
    """Test handling of AttributeError leads to raising AmazonBraketVersionError."""
    mock_aws_quantum_task.return_value.queue_position.side_effect = AttributeError
    job = BraketQuantumTask("job_id")
    with pytest.raises(AmazonBraketVersionError) as excinfo:
        job.queue_position()
    assert "Queue visibility is only available for amazon-braket-sdk>=1.56.0" in str(excinfo.value)


def test_job_raise_for_cancel_terminal():
    """Test raising an error when trying to cancel a completed/failed job."""
    with patch("qbraid.runtime.job.QuantumJob.is_terminal_state", return_value=True):
        job = BraketQuantumTask(SV1_ARN, task=Mock())
        with pytest.raises(JobStateError):
            job.cancel()


def test_result_measurements():
    """Test measurements method of BraketGateModelResultBuilder class."""
    mock_measurements = np.array([[0, 1, 1], [1, 0, 1]])
    mock_result = MagicMock()
    mock_result.measurements = mock_measurements
    result = BraketGateModelResultBuilder(mock_result)
    expected_output = np.array([[1, 1, 0], [1, 0, 1]])
    np.testing.assert_array_equal(result.measurements(), expected_output)


def test_result_get_counts():
    """Test get_counts method of BraketGateModelResultBuilder class."""
    mock_measurement_counts = {(0, 1, 1): 10, (1, 0, 1): 5}
    mock_result = MagicMock()
    mock_result.measurement_counts = mock_measurement_counts
    result = BraketGateModelResultBuilder(mock_result)
    expected_output = {"110": 10, "101": 5}
    assert result.get_counts() == expected_output


def test_get_default_region_error():
    """Test getting default region when an exception is raised."""
    with patch("qbraid.runtime.aws.provider.Session") as mock_boto_session:
        mock_boto_session.side_effect = Exception
        mock_boto_session.region_name.return_value = "not us-east-1"
        assert BraketProvider()._get_default_region() == "us-east-1"


def test_get_s3_default_bucket():
    """Test getting default S3 bucket."""
    with patch("qbraid.runtime.aws.provider.AwsSession") as mock_aws_session:
        mock_instance = mock_aws_session.return_value
        mock_instance.default_bucket.return_value = "default bucket"
        assert BraketProvider()._get_s3_default_bucket() == "default bucket"

        mock_instance.default_bucket.side_effect = Exception
        assert BraketProvider()._get_s3_default_bucket() == "amazon-braket-qbraid-jobs"


def test_get_quantum_task_cost():
    """Test getting quantum task cost."""
    task_mock = Mock()
    task_mock.arn = "fake_arn"
    task_mock.state.return_value = "COMPLETED"
    job = BraketQuantumTask("task_arn", task_mock)
    with patch("qbraid.runtime.aws.job.get_quantum_task_cost", return_value=0.1):
        assert job.get_cost() == 0.1


def test_built_runtime_profile_fail():
    """Test building a runtime profile with invalid device."""

    class FakeSession:
        """Fake Session for testing."""

        def __init__(self):
            self.region = "us-east-1"

        def get_device(self, arn):  # pylint: disable=unused-argument
            """Fake get_device method."""
            return {
                "deviceType": "SIMULATOR",
                "providerName": "Amazon Braket",
                "deviceCapabilities": "{}",
            }

    class FakeDevice:
        """Fake AWS Device for testing."""

        def __init__(self, arn, aws_session=None):
            self.arn = arn
            self.aws_session = aws_session or FakeSession()
            self.status = "ONLINE"
            self.properties = TestProperties()
            self.is_available = True

        @staticmethod
        def get_device_region(arn):  # pylint: disable=unused-argument
            """Fake get_device_region method."""
            return "us-east-1"

    provider = BraketProvider(
        aws_access_key_id="aws_access_key_id",
        aws_secret_access_key="aws_secret_access_key",
    )

    device = FakeDevice(arn=SV1_ARN, aws_session=FakeSession())
    with pytest.raises(QbraidError):
        assert provider._build_runtime_profile(device=device)


def test_braket_result_error():
    """Test Braket result decoding error."""
    task = MockTask("task1")
    braket_task = BraketQuantumTask("task1", task)
    with pytest.raises(ValueError):
        braket_task.result()


def test_braket_job_cancel():
    """Test Braket job cancel method."""
    task = MockTask("task2")
    braket_task = BraketQuantumTask("task2", task)
    assert braket_task.cancel() is None


def test_get_tasks_by_tag_value_error():
    """Test getting tagged quantum tasks with invalid values."""
    with patch("qbraid.runtime.aws.provider.quantum_lib_proxy_state") as mock_proxy_state:
        mock_proxy_state.side_effect = ValueError

        provider = BraketProvider()

        try:
            result = provider.get_tasks_by_tag("key", ["value1", "value2"])
        except NoCredentialsError:
            pytest.skip("NoCredentialsError raised")

        assert isinstance(result, list)


def test_get_tasks_by_tag_qbraid_error():
    """Test getting tagged quantum tasks with jobs enabled."""
    with patch("qbraid.runtime.aws.provider.quantum_lib_proxy_state") as mock_proxy_state:
        mock_proxy_state.return_value = {"enabled": True}

        provider = BraketProvider()

        with pytest.raises(QbraidError):
            provider.get_tasks_by_tag("key", ["value1", "value2"])


@pytest.fixture
def mock_braket_provider_with_credentials():
    """Return a BraketProvider instance with mock credentials."""
    aws_provider = BraketProvider(
        aws_access_key_id="mock_access_key_id",
        aws_secret_access_key="mock_secret_access_key",
        aws_session_token="mock_session_token",
    )
    return aws_provider


@patch("builtins.hash", autospec=True)
def test_hash_method_creates_and_returns_hash(mock_hash, mock_braket_provider_with_credentials):
    """Test that the __hash__ method creates and returns a hash value."""
    mock_hash.return_value = 5555
    provider_instance = mock_braket_provider_with_credentials
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    mock_hash.assert_called_once_with(
        ("mock_access_key_id", "mock_secret_access_key", "mock_session_token")
    )
    assert result == 5555
    assert provider_instance._hash == 5555


def test_hash_method_returns_existing_hash(mock_braket_provider_with_credentials):
    """Test that the __hash__ method returns the existing hash value."""
    provider_instance = mock_braket_provider_with_credentials
    provider_instance._hash = 9876
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    assert result == 9876

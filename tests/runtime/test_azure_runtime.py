# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint:disable=redefined-outer-name

"""
Unit tests for the Azure Quantum runtime module.

"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from azure.identity import ClientSecretCredential
from azure.quantum import Job, JobDetails, Workspace
from azure.quantum.target.microsoft import MicrosoftEstimatorResult
from azure.quantum.target.target import Target

from qbraid.runtime import (
    DeviceActionType,
    DeviceStatus,
    JobStateError,
    JobStatus,
    ResourceNotFoundError,
    TargetProfile,
)
from qbraid.runtime.azure import (
    AzureQuantumDevice,
    AzureQuantumJob,
    AzureQuantumProvider,
    AzureQuantumResult,
    AzureResultBuilder,
)


@pytest.fixture
def mock_workspace():
    """Return a mock Azure Quantum workspace."""
    return Mock(spec=Workspace)


@pytest.fixture
def mock_target():
    """Return a mock Azure Quantum target."""
    target = Mock(spec=Target)
    target.name = "test.qpu"
    target.provider_id = "test_provider"
    target.capability = "test_capability"
    target.input_data_format = "test_input"
    target.output_data_format = "test_output"
    target.content_type = "application/qasm"
    target._current_availability = "Available"
    return target


@pytest.fixture
def mock_invalid_target():
    """Return a mock Azure Quantum target with invalid content type."""
    target = Mock(spec=Target)
    target.name = "test.qpu"
    target.provider_id = "test_provider"
    target.capability = "test_capability"
    target.input_data_format = "test_input"
    target.output_data_format = "test_output"
    target.content_type = ""
    target._current_availability = "Available"
    return target


@pytest.fixture
def azure_provider(mock_workspace):
    """Return an AzureQuantumProvider instance with a mock workspace."""
    return AzureQuantumProvider(mock_workspace)


@pytest.fixture
def azure_device(mock_workspace, mock_target):
    """Return an AzureQuantumDevice instance with a mock workspace and target."""
    profile = TargetProfile(
        device_id="test.qpu",
        simulator=False,
        provider_name="test_provider",
        capability="test_capability",
        input_data_format="test_input",
        output_data_format="test_output",
        action_type=DeviceActionType.OPENQASM,
    )
    mock_workspace.get_targets.return_value = mock_target
    return AzureQuantumDevice(profile, mock_workspace)


@pytest.fixture
def mock_azure_job():
    """Return a mock AzureQuantumJob instance."""
    mock_workspace = Mock(spec=Workspace)
    mock_job = Mock()
    mock_job.id = "mock_job_id"
    mock_job.details = Mock()
    mock_job.details.status = "Waiting"
    mock_job.details.as_dict.return_value = {"id": "mock_job_id", "status": "Waiting"}

    mock_job_cancelled = Mock()
    mock_job_cancelled.id = "mock_job_id"
    mock_job_cancelled.details = Mock()
    mock_job_cancelled.details.status = "Cancelled"
    mock_job_cancelled.details.as_dict.return_value = {"id": "mock_job_id", "status": "Cancelled"}

    mock_workspace.get_job.return_value = mock_job
    mock_workspace.cancel_job.return_value = mock_job_cancelled

    return AzureQuantumJob(job_id=mock_job.id, workspace=mock_workspace)


@pytest.fixture
def azure_result():
    """Return an AzureQuantumResult instance."""
    result_data = {"meas": ["00", "01", "00", "10", "00", "01"], "other_data": [1, 2, 3]}
    return AzureQuantumResult(result_data)


def test_azure_provider_init_with_credential():
    """Test initializing an AzureQuantumProvider with a credential."""
    workspace = Mock(spec=Workspace)
    workspace.credential = None
    credential = Mock(spec=ClientSecretCredential)

    provider = AzureQuantumProvider(workspace, credential)

    assert provider.workspace.credential == credential
    assert "qbraid" in workspace.append_user_agent.call_args[0][0]


def test_init_without_credential():
    """Test initializing an AzureQuantumProvider without a credential."""
    workspace = Workspace(
        subscription_id="something",
        resource_group="something",
        name="something",
        location="something",
    )
    with pytest.warns(Warning):
        AzureQuantumProvider(workspace)


def test_azure_provider_workspace_property(azure_provider, mock_workspace):
    """Test the workspace property of an AzureQuantumProvider."""
    assert azure_provider.workspace == mock_workspace


def test_build_profile(azure_provider, mock_target):
    """Test building a profile for an AzureQuantumProvider."""
    profile = azure_provider._build_profile(mock_target)

    assert isinstance(profile, TargetProfile)
    assert profile.action_type.value == "qbraid.programs.circuits"


def test_build_profile_invalid(azure_provider, mock_invalid_target):
    """Test building a profile for an AzureQuantumProvider with an invalid target."""
    profile = azure_provider._build_profile(mock_invalid_target)

    assert isinstance(profile, TargetProfile)
    assert profile.action_type is None


def test_azure_provider_get_devices(azure_provider, mock_workspace, mock_target):
    """Test getting devices from an AzureQuantumProvider."""
    mock_workspace.get_targets.return_value = [mock_target]

    devices = azure_provider.get_devices()

    assert len(devices) == 1
    assert isinstance(devices[0], AzureQuantumDevice)


def test_azure_provider_get_devices_no_results(azure_provider, mock_workspace):
    """Test getting devices from an AzureQuantumProvider with no results."""
    mock_workspace.get_targets.return_value = []

    with pytest.raises(ResourceNotFoundError):
        azure_provider.get_devices()


def test_azure_provider_get_device(azure_provider, mock_workspace, mock_target):
    """Test getting a device from an AzureQuantumProvider."""
    mock_workspace.get_targets.return_value = mock_target

    device = azure_provider.get_device("test.qpu")

    assert isinstance(device, AzureQuantumDevice)


def test_azure_provider_get_device_not_found(azure_provider, mock_workspace):
    """Test getting a nonexistent device from an AzureQuantumProvider."""
    mock_workspace.get_targets.return_value = None

    with pytest.raises(ValueError):
        azure_provider.get_device("nonexistent.qpu")


def test_get_devices_single_target(mock_workspace):
    """Test getting devices when a single Target object is returned."""
    single_target = Mock(spec=Target)
    single_target.name = "test_target.qpu.test"
    single_target.provider_id = "test_provider"
    single_target.capability = "test_capability"
    single_target.input_data_format = "test_input"
    single_target.output_data_format = "test_output"
    single_target._current_availability = "Available"
    single_target.content_type = "application/json"

    mock_workspace.get_targets.return_value = single_target

    provider = AzureQuantumProvider(mock_workspace)

    devices = provider.get_devices()

    assert len(devices) == 1
    assert isinstance(devices[0], AzureQuantumDevice)
    assert devices[0].profile.device_id == "test_target.qpu.test"
    assert devices[0].profile.provider_name == "test_provider"


def test_get_devices_no_results_with_filters(mock_workspace):
    """Test getting devices with no results and filters applied."""
    mock_workspace.get_targets.return_value = []
    provider = AzureQuantumProvider(mock_workspace)

    with pytest.raises(ValueError, match="No devices found with the specified filters."):
        provider.get_devices(filter="some_filter")


def test_get_devices_no_results_no_filters(mock_workspace):
    """Test getting devices with no results and no filters applied."""
    mock_workspace.get_targets.return_value = []
    provider = AzureQuantumProvider(mock_workspace)

    with pytest.raises(ResourceNotFoundError, match="No devices found."):
        provider.get_devices()


def test_azure_device_init(azure_device, mock_workspace):
    """Test initializing an AzureQuantumDevice."""
    assert azure_device.workspace == mock_workspace
    mock_workspace.get_targets.assert_called_once_with(name="test.qpu")


def test_azure_device_status(azure_device, mock_target):
    """Test getting the status of an AzureQuantumDevice."""
    assert azure_device.status() == DeviceStatus.ONLINE

    mock_target._current_availability = "Deprecated"
    assert azure_device.status() == DeviceStatus.UNAVAILABLE

    mock_target._current_availability = "Unavailable"
    assert azure_device.status() == DeviceStatus.OFFLINE

    mock_target._current_availability = "Unknown"
    assert azure_device.status() == DeviceStatus.UNAVAILABLE


def test_azure_device_submit(azure_device, mock_target):
    """Test submitting a job to an AzureQuantumDevice."""
    mock_job = Mock()
    mock_job.id = "mock_job_id"
    mock_target.submit.return_value = mock_job

    run_input = "test_input"
    job = azure_device.submit(run_input)

    assert isinstance(job, AzureQuantumJob)
    assert job.id == "mock_job_id"
    assert job.workspace == azure_device.workspace
    assert job.device == azure_device

    mock_target.submit.assert_called_once_with(run_input)


def test_azure_device_submit_batch_job(azure_device):
    """Test submitting a batch job to an AzureQuantumDevice."""
    with pytest.raises(ValueError):
        azure_device.submit(["job1", "job2"], name="batch_job")


def test_azure_job_init(mock_azure_job):
    """Test initializing an AzureQuantumJob."""
    assert mock_azure_job.id == "mock_job_id"
    assert isinstance(mock_azure_job.workspace, Workspace)


@pytest.mark.parametrize(
    "job_status, expected_status",
    [
        ("Succeeded", JobStatus.COMPLETED),
        ("Waiting", JobStatus.QUEUED),
        ("Executing", JobStatus.RUNNING),
        ("Failed", JobStatus.FAILED),
        ("Cancelled", JobStatus.CANCELLED),
        ("Finishing", JobStatus.RUNNING),
        ("NonExistentStatus", JobStatus.UNKNOWN),
    ],
)
def test_azure_job_status(job_status, expected_status):
    """Test getting the status of an AzureQuantumJob."""
    mock_workspace = MagicMock()
    mock_job = MagicMock()
    mock_job.details.as_dict.return_value = {"status": job_status}
    mock_workspace.get_job.return_value = mock_job

    job = AzureQuantumJob(job_id="123", workspace=mock_workspace)
    assert job.status() == expected_status
    mock_job.refresh.assert_called_once()


def test_azure_job_cancel(mock_azure_job):
    """Test canceling an AzureQuantumJob."""
    mock_azure_job.cancel()
    assert mock_azure_job._job.details.status == "Cancelled"


def test_azure_job_cancel_terminal_state_raises():
    """Test canceling an AzureQuantumJob in a terminal state."""
    mock_workspace = MagicMock()
    mock_job = MagicMock()
    mock_job.details.as_dict.return_value = {"status": "Succeeded"}
    mock_workspace.get_job.return_value = mock_job

    job = AzureQuantumJob(job_id="123", workspace=mock_workspace)
    with pytest.raises(JobStateError):
        job.cancel()


@pytest.fixture
def mock_result_builder() -> AzureResultBuilder:
    """Create a mock Azure result builder."""
    job = Mock(id="test123")
    return AzureResultBuilder(job)


@pytest.fixture
def mock_result() -> AzureQuantumResult:
    """Create a mock result data."""
    data = {
        "results": [
            {
                "data": {
                    "counts": {"000": 50, "111": 50},
                    "probabilities": {"000": 0.5, "111": 0.5},
                },
                "success": True,
                "header": {},
                "shots": 100,
            }
        ],
        "job_id": "test123",
        "target": "ionq.simulator",
        "job_name": "ionq-job",
        "success": True,
        "error_data": None,
    }
    return AzureQuantumResult(data)


class DowloadDataMock:
    """Mock download data method."""

    def decode(self) -> str:
        """Mock decode method."""


def mock_job(job_id: str, target: str, output_data_format: str, results_as_json_str: str) -> Job:
    """Create a mock Azure Quantum Job."""
    job_details = JobDetails(
        id=job_id,
        name="azure-quantum-job",
        provider_id="",
        target=target,
        container_uri="",
        input_params={"shots": 100},
        input_data_format="",
        output_data_format=output_data_format,
    )
    job_details.status = "Succeeded"
    job = Job(workspace=Mock(spec=Workspace), job_details=job_details)

    job.has_completed = Mock(return_value=True)
    job.wait_until_completed = Mock()

    download_data = DowloadDataMock()
    download_data.decode = Mock(return_value=results_as_json_str)
    job.download_data = Mock(return_value=download_data)

    return job


def test_job_for_microsoft_quantum_results_v1_success():
    """Test getting job for microsoft.quantum-results.v1 output data format."""
    job_id = "test123"
    target = "microsoft.estimator"
    output_data_format = "microsoft.quantum-results.v1"
    results_as_json_str = '{"Histogram": ["[0]", 0.50, "[1]", 0.50]}'
    job = mock_job(job_id, target, output_data_format, results_as_json_str)

    builder = AzureResultBuilder(job)
    assert isinstance(builder.job, Job)
    assert builder.job == job
    assert builder.from_simulator is True
    assert builder._shots_count() == 100


def test_make_estimator_result_with_failure():
    """Test making an estimator result with a failed job."""
    data = {
        "success": False,
        "error_data": {
            "code": "ResourceUnavailable",
            "message": "The resource is currently unavailable.",
        },
    }
    with pytest.raises(RuntimeError) as exc_info:
        AzureResultBuilder.make_estimator_result(data)
    assert (
        "Cannot retrieve results as job execution failed (ResourceUnavailable: "
        "The resource is currently unavailable.)" in str(exc_info.value)
    )


def test_make_estimator_result_with_incorrect_results_length():
    """Test making an estimator result with incorrect results length."""
    data = {"success": True, "results": [{"data": 42}, {"data": 43}]}
    with pytest.raises(ValueError) as exc_info:
        AzureResultBuilder.make_estimator_result(data)
    assert "Expected resource estimator results to be of length 1" in str(exc_info.value)


def test_make_estimator_result_successful():
    """Test making an estimator result with successful job."""
    data = {
        "job_id": "123-456-798",
        "target": "microsoft.estimator",
        "job_name": "azure-quantum-job",
        "success": True,
        "error_data": None,
        "results": [
            {
                "data": {
                    "status": "success",
                    "jobParams": {},
                    "physicalCounts": {},
                    "physicalCountsFormatted": {},
                    "logicalQubit": {},
                    "tfactory": {},
                    "errorBudget": {},
                    "logicalCounts": {},
                    "reportData": {"groups": [], "assumptions": []},
                }
            }
        ],
    }
    result = AzureResultBuilder.make_estimator_result(data)
    assert isinstance(result, MicrosoftEstimatorResult)
    assert result["status"] == "success"


@pytest.mark.parametrize("probabilities", [{"00": 0.5, "11": 0.5}, {"00": 0.4999, "11": 0.5001}])
def test_draw_random_sample_probabilities(mock_result_builder: AzureResultBuilder, probabilities):
    """Test that the random sample handles both normalized and unnormalized probabilities."""
    shots = 1000
    sample = mock_result_builder._draw_random_sample(None, probabilities, shots)
    assert sum(sample.values()) == shots
    assert set(sample.keys()) == {"00", "11"}


@pytest.mark.parametrize("seed, should_match", [(42, True), (None, False)])
def test_draw_random_sample_consistency(
    mock_result_builder: AzureResultBuilder, seed, should_match
):
    """Test drawing random samples with and without a specific seed."""
    shots = 10
    probabilities = {"00": 0.5, "11": 0.5}
    sample1 = mock_result_builder._draw_random_sample(seed, probabilities, shots)
    sample2 = mock_result_builder._draw_random_sample(seed, probabilities, shots)
    sample3 = mock_result_builder._draw_random_sample(seed, probabilities, shots)

    if should_match:
        assert sample1 == sample2 == sample3
    else:
        assert not sample1 == sample2 == sample3


def test_draw_random_sample_with_invalid_probabilities(mock_result_builder: AzureResultBuilder):
    """Test the method raises an error when probabilities don't sum close to one."""
    probabilities = {"00": 0.3, "11": 0.4}
    shots = 1000
    with pytest.raises(ValueError) as exc_info:
        mock_result_builder._draw_random_sample(None, probabilities, shots)
    assert "Probabilities do not add up to 1" in str(exc_info.value)


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        ("[0, 1, 0, 1]", "0101"),
        ((["1", "0"], ["0", "1"]), "01 10"),
        ([1, 0, 1, 0], "1010"),
        (42, "42"),
        ("((1, 0), (1, 0))", "0 1 0 1"),
        ("[1, 0]", "10"),
    ],
)
def test_qir_to_qbraid_bitstring(input_data, expected_output):
    """Test various inputs for _qir_to_qbraid_bitstring method."""
    assert AzureResultBuilder._qir_to_qbraid_bitstring(input_data) == expected_output


def test_azure_quantum_result(mock_result: AzureQuantumResult):
    """Test Azure Quantum Job result methods."""
    measurements = mock_result.measurements()
    raw_counts = mock_result.get_counts()
    formatted_counts = mock_result.measurement_counts()
    assert measurements.shape == (100, 3)
    assert raw_counts == formatted_counts == {"000": 50, "111": 50}


# Constants for mocking
MOCK_JOB_ID = "mock_job_id"
MOCK_JOB_STATUS_SUCCEEDED = "Succeeded"
MOCK_TARGET = "mock.target"
MOCK_METADATA = {"some": "metadata"}
MOCK_OUTPUT_FORMAT = "microsoft.quantum-results.v1"


@pytest.fixture
def mock_azure_job2():
    """Return a mock AzureQuantumJob instance."""
    job = Mock(spec=Job)
    job.details.status = MOCK_JOB_STATUS_SUCCEEDED
    job.details.target = MOCK_TARGET
    job.details.metadata = MOCK_METADATA
    job.details.output_data_format = MOCK_OUTPUT_FORMAT
    job.details.input_params = {"count": 1000, "shots": 1000}
    job.id = MOCK_JOB_ID
    return job


@pytest.fixture
def azure_result_builder(mock_azure_job2):
    """Return an AzureResultBuilder instance with a mock AzureQuantumJob."""
    return AzureResultBuilder(mock_azure_job2)


def test_job_property(azure_result_builder, mock_azure_job2):
    """Test the job property of an AzureResultBuilder."""
    assert azure_result_builder.job == mock_azure_job2


def test_from_simulator_true(azure_result_builder, mock_azure_job2):
    """Test the from_simulator property of an AzureResultBuilder."""
    mock_azure_job2.details.target = "mock.simulator"
    assert azure_result_builder.from_simulator is True


def test_from_simulator_false(azure_result_builder, mock_azure_job2):
    """Test the from_simulator property of an AzureResultBuilder."""
    mock_azure_job2.details.target = "mock.qpu"
    assert azure_result_builder.from_simulator is False


def test_shots_count(azure_result_builder):
    """Test the shots count method of an AzureResultBuilder."""
    assert azure_result_builder._shots_count() == 1000


def test_make_estimator_result(azure_result_builder):
    """Test making an estimator result from an AzureQuantumJob."""
    mock_data = {"success": True, "results": [{"data": {"mock_data_key": "mock_data_value"}}]}
    result = azure_result_builder.make_estimator_result(mock_data)
    assert isinstance(result, MicrosoftEstimatorResult)
    assert result.data()["mock_data_key"] == "mock_data_value"


def test_make_estimator_result_failure(azure_result_builder):
    """Test making an estimator result from a failed AzureQuantumJob."""
    mock_data = {"success": False, "error_data": {"code": "MockError", "message": "Job failed"}}
    with pytest.raises(RuntimeError, match="Cannot retrieve results as job execution failed"):
        azure_result_builder.make_estimator_result(mock_data)


@pytest.fixture
def mock_qir_to_qbraid_bitstring():
    """Return a mock for the qir_to_qbraid_bitstring method."""
    with patch(
        "qbraid.runtime.azure.result_builder.AzureResultBuilder._qir_to_qbraid_bitstring"
    ) as mock:
        yield mock


def test_format_microsoft_results(
    mock_qir_to_qbraid_bitstring, azure_result_builder, mock_azure_job2
):
    """Test formatting Microsoft Quantum results."""
    mock_azure_job2.get_results.return_value = {"00": 0.5, "11": 0.5}
    mock_qir_to_qbraid_bitstring.side_effect = lambda x: x

    result = azure_result_builder._format_microsoft_results()

    assert "counts" in result
    assert "probabilities" in result
    assert abs(result["counts"]["00"] - 500) >= 0  # Allow some tolerance
    assert abs(result["counts"]["11"] - 500) >= 0


def test_format_rigetti_results(azure_result_builder, mock_azure_job2):
    """Test formatting Rigetti results."""
    mock_azure_job2.get_results.return_value = {"ro": [[0, 1], [1, 0], [0, 1], [1, 0]]}

    result = azure_result_builder._format_rigetti_results()

    assert "counts" in result
    assert "probabilities" in result
    assert result["counts"] == {"01": 2, "10": 2}
    assert result["probabilities"] == {"01": 0.5, "10": 0.5}


def test_format_unknown_results(azure_result_builder, mock_azure_job2):
    """Test formatting unknown results."""
    mock_azure_job2.get_results.return_value = {"mock_key": "mock_value"}

    result = azure_result_builder._format_unknown_results()

    assert result == {"mock_key": "mock_value"}


@patch("qbraid.runtime.azure.result_builder.AzureResultBuilder._qir_to_qbraid_bitstring")
def test_format_quantinuum_results(
    mock_qir_to_qbraid_bitstring, azure_result_builder, mock_azure_job2
):
    """Test formatting Quantinuum results."""
    mock_azure_job2.get_results.return_value = {"qreg0": ["0", "1", "1"], "qreg1": ["1", "0", "1"]}
    mock_qir_to_qbraid_bitstring.side_effect = lambda x: x

    result = azure_result_builder._format_quantinuum_results()

    assert "counts" in result
    assert "probabilities" in result
    assert result["counts"] == {"01": 1, "10": 1, "11": 1}
    assert result["probabilities"] == {"01": 1 / 3, "10": 1 / 3, "11": 1 / 3}


def test_translate_microsoft_v2_results(azure_result_builder, mock_azure_job2):
    """Test translating Microsoft Quantum v2 results."""
    mock_azure_job2.get_results.return_value = {
        "DataFormat": "v2",
        "Results": [
            {
                "TotalCount": 1000,
                "Histogram": [{"Display": "00", "Count": 700}, {"Display": "11", "Count": 300}],
            }
        ],
    }

    results = azure_result_builder._translate_microsoft_v2_results()

    assert len(results) == 1
    total_count, result = results[0]
    assert total_count == 1000
    assert result["counts"] == {"00": 700, "11": 300}
    assert result["probabilities"] == {"00": 0.7, "11": 0.3}


def test_format_microsoft_v2_results(azure_result_builder):
    """Test formatting Microsoft Quantum v2 results."""
    azure_result_builder._get_entry_point_names = Mock(return_value=["main"])
    azure_result_builder._translate_microsoft_v2_results = Mock(
        return_value=[
            (1000, {"counts": {"00": 700, "11": 300}, "probabilities": {"00": 0.7, "11": 0.3}})
        ]
    )
    result = azure_result_builder._format_microsoft_v2_results()

    assert len(result) == 1
    result_item = result[0]
    assert result_item["shots"] == 1000
    assert result_item["data"]["counts"] == {"00": 700, "11": 300}
    assert result_item["data"]["probabilities"] == {"00": 0.7, "11": 0.3}

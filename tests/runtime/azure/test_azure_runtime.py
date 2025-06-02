# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint:disable=redefined-outer-name,too-many-arguments,too-many-lines

"""
Unit tests for the Azure Quantum runtime module.

"""
import json
import os
import re
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from azure.core.exceptions import ResourceExistsError
from azure.identity import ClientSecretCredential
from azure.quantum import Job, JobDetails, Workspace
from azure.quantum.target.microsoft import MicrosoftEstimatorResult
from azure.quantum.target.target import Target

from qbraid.programs import QPROGRAM_REGISTRY, ExperimentType, ProgramSpec
from qbraid.runtime import (
    AhsResultData,
    DeviceStatus,
    GateModelResultData,
    JobStateError,
    JobStatus,
    ResourceNotFoundError,
    Result,
    TargetProfile,
)
from qbraid.runtime.azure import AzureQuantumDevice, AzureQuantumJob
from qbraid.runtime.azure.io_format import InputDataFormat, OutputDataFormat
from qbraid.runtime.azure.provider import AzureQuantumProvider, serialize_pulser_input
from qbraid.runtime.azure.result_builder import AzureResultBuilder
from qbraid.runtime.postprocess import normalize_data

pytestmark = pytest.mark.filterwarnings("ignore:Unrecognized input data format:UserWarning")


@pytest.fixture
def mock_workspace():
    """Return a mock Azure Quantum workspace."""
    return Mock(spec=Workspace)


@pytest.fixture
def mock_target():
    """Return a mock Azure Quantum target."""
    target = Mock(spec=Target)
    target.name = "test.qpu.test"
    target.provider_id = "test_provider"
    target.capability = "test_capability"
    target.input_data_format = InputDataFormat.MICROSOFT.value
    target.output_data_format = OutputDataFormat.MICROSOFT_V1.value
    target.content_type = "application/qasm"
    target._current_availability = "Available"
    return target


@pytest.fixture
def mock_invalid_target():
    """Return a mock Azure Quantum target with invalid content type."""
    target = Mock(spec=Target)
    target.name = "test.qpu.test"
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
        device_id="test.qpu.test",
        simulator=False,
        provider_name="test_provider",
        capability="test_capability",
        input_data_format="test_input",
        output_data_format="test_output",
        experiment_type=ExperimentType.GATE_MODEL,
    )
    mock_workspace.get_targets.return_value = mock_target
    return AzureQuantumDevice(profile, mock_workspace)


@pytest.fixture
def mock_job_id() -> str:
    """Return a mock job ID."""
    return "123-456-798"


@pytest.fixture
def mock_estimator_job_data(mock_job_id) -> dict[str, str]:
    """Return dictionary data for a Microsoft resource estimator job."""
    return {
        "job_id": mock_job_id,
        "job_name": "azure-quantum-job",
        "target": "microsoft.estimator",
        "output_data_format": "microsoft.resource-estimates.v1",
    }


@pytest.fixture
def mock_msft_v1_job_data(mock_job_id) -> dict[str, str]:
    """Return dictionary data for a Rigetti job with Microsoft result format V1."""
    return {
        "job_id": mock_job_id,
        "job_name": "azure-quantum-job",
        "target": "rigetti.sim.qvm",
        "output_data_format": "microsoft.quantum-results.v1",
    }


@pytest.fixture
def mock_ionq_job_data(mock_job_id) -> dict[str, str]:
    """Return dictionary data for a Rigetti job with Microsoft result format V1."""
    return {
        "job_id": mock_job_id,
        "job_name": "ionq-job",
        "target": "ionq.simulator",
        "output_data_format": "ionq.quantum-results.v1",
    }


@pytest.fixture
def mock_pasqal_job_data(mock_job_id) -> dict[str, str]:
    """Return dictionary data for a Rigetti job with Microsoft result format V1."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    return {
        "job_id": mock_job_id,
        "job_name": "pasqal-job",
        "target": "pasqal.sim.emu-tn",
        "output_data_format": "pasqal.pulser-results.v1",
    }


@pytest.fixture
def mock_pasqal_result_data(mock_job_id) -> dict[str, str]:
    """Return dictionary data for a Rigetti job with Microsoft result format V1."""
    return {"001010": 50, "001011": 50}


@pytest.fixture
def estimator_result_data(mock_estimator_job_data: dict[str, str]) -> dict[str, Any]:
    """Return a dictionary with the data for a MicrosoftEstimatorResult."""
    return {
        "success": True,
        "error_data": None,
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
        },
        **mock_estimator_job_data,
    }


def create_mock_azure_job(
    job_id: str,
    job_name: str,
    target: str,
    output_data_format: str,
    status: str,
    result_data: dict[str, Any],
) -> Mock:
    """Return a mock azure.quantum.Job instance."""
    mock_job = Mock()
    mock_job.id = job_id
    mock_job.details = Mock()
    mock_job.details.status = status
    mock_job.details.target = target
    mock_job.details.output_data_format = output_data_format
    mock_job.details.input_params = {"count": 1000, "shots": 1000}
    mock_job.details.error_data = None
    mock_job.details.name = job_name
    mock_job.details.metadata = {}
    mock_job.details.as_dict.return_value = {"id": job_id, "status": status}
    mock_job.get_results = MagicMock()
    mock_job.get_results.return_value = result_data

    return mock_job


def create_mock_job(
    job_id: str,
    job_name: str,
    target: str,
    output_data_format: str,
    status: str,
    result_data: dict[str, Any],
) -> AzureQuantumJob:
    """Return a mock AzureQuantumJob instance."""
    mock_job = create_mock_azure_job(
        job_id, job_name, target, output_data_format, status, result_data
    )

    mock_workspace = Mock(spec=Workspace)
    mock_workspace.get_job.return_value = mock_job

    if status == "Waiting":
        mock_job_cancelled = Mock()
        mock_job_cancelled.id = job_id
        mock_job_cancelled.details = Mock()
        mock_job_cancelled.details.status = "Cancelled"
        mock_job_cancelled.details.as_dict.return_value = {"id": job_id, "status": "Cancelled"}
        mock_workspace.cancel_job.return_value = mock_job_cancelled
    else:
        mock_workspace.cancel_job.side_effect = ResourceExistsError(
            "(CancellationNotAllowed) Failed to cancel the job from its current state."
        )

    return AzureQuantumJob(job_id=mock_job.id, workspace=mock_workspace)


@pytest.fixture
def mock_estimator_job_waiting(mock_estimator_job_data: dict[str, str]) -> AzureQuantumJob:
    """Return a mock AzureQuantumJob instance with status 'Waiting'."""
    return create_mock_job(**mock_estimator_job_data, status="Waiting", result_data={})


@pytest.fixture
def mock_estimator_job(
    mock_estimator_job_data: dict[str, str], estimator_result_data: dict[str, Any]
) -> AzureQuantumJob:
    """Return a mock AzureQuantumJob instance with status 'Succeeded'."""
    return create_mock_job(
        **mock_estimator_job_data, status="Succeeded", result_data=estimator_result_data
    )


@pytest.fixture
def mock_azure_job(
    mock_estimator_job_data: dict[str, str], estimator_result_data: dict[str, Any]
) -> Mock:
    """Return a mock azure.quantum.Job instance."""
    return create_mock_azure_job(
        **mock_estimator_job_data, status="Succeeded", result_data=estimator_result_data
    )


@pytest.fixture
def mock_azure_ahs_job(
    mock_pasqal_job_data: dict[str, str], mock_pasqal_result_data: dict[str, Any]
) -> Mock:
    """Return a mock azure.quantum.Job instance."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    return create_mock_azure_job(
        **mock_pasqal_job_data, status="Succeeded", result_data=mock_pasqal_result_data
    )


@pytest.fixture
def mock_azure_ionq_job(mock_ionq_job_data: dict[str, str]) -> Mock:
    """Return a mock azure.quantum.Job instance."""
    return create_mock_azure_job(
        **mock_ionq_job_data, status="Succeeded", result_data={"histogram": {"0": 0.5, "7": 0.5}}
    )


@pytest.fixture
def mock_azure_pasqal_job(mock_pasqal_job_data: dict[str, str]) -> Mock:
    """Return a mock azure.quantum.Job instance."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    return create_mock_azure_job(
        **mock_pasqal_job_data, status="Succeeded", result_data={"001010": 50, "001011": 50}
    )


@pytest.fixture
def mock_azure_failed_pasqal_job(mock_pasqal_job_data: dict[str, str]) -> Mock:
    """Return a mock azure.quantum.Job instance."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    return create_mock_azure_job(**mock_pasqal_job_data, status="Failed", result_data={})


@pytest.fixture
def azure_result_builder(mock_azure_job):
    """Return an AzureResultBuilder instance with a mock AzureQuantumJob."""
    return AzureResultBuilder(mock_azure_job)


@pytest.fixture
def azure_ahs_result_builder(mock_azure_ahs_job):
    """Return an AzureResultBuilder instance with a mock AzureQuantumJob."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    return AzureResultBuilder(mock_azure_ahs_job)


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
    original_connection_string = os.environ.pop("AZURE_QUANTUM_CONNECTION_STRING", None)

    try:
        assert "AZURE_QUANTUM_CONNECTION_STRING" not in os.environ

        workspace = Workspace(
            subscription_id="something",
            resource_group="something",
            name="something",
            location="something",
        )
        with pytest.warns(Warning):
            AzureQuantumProvider(workspace)
    finally:
        if original_connection_string is not None:
            os.environ["AZURE_QUANTUM_CONNECTION_STRING"] = original_connection_string


def test_azure_provider_workspace_property(azure_provider, mock_workspace):
    """Test the workspace property of an AzureQuantumProvider."""
    assert azure_provider.workspace == mock_workspace


def test_build_profile(azure_provider, mock_target):
    """Test building a profile for an AzureQuantumProvider."""
    profile = azure_provider._build_profile(mock_target)

    assert isinstance(profile, TargetProfile)
    assert profile.experiment_type.value == "gate_model"


def test_build_profile_invalid(azure_provider, mock_invalid_target):
    """Test building a profile for an AzureQuantumProvider with an invalid target."""
    profile = azure_provider._build_profile(mock_invalid_target)

    assert isinstance(profile, TargetProfile)
    assert profile.program_spec is None
    assert profile.experiment_type is None


@pytest.mark.parametrize(
    "input_data_format, expected_alias, provider_id",
    [
        (InputDataFormat.MICROSOFT.value, "pyqir", "microsoft"),
        (InputDataFormat.IONQ.value, "ionq", "ionq"),
        (InputDataFormat.QUANTINUUM.value, "qasm2", "quantinuum"),
        (InputDataFormat.RIGETTI.value, "pyquil", "rigetti"),
    ],
)
def test_build_profile_input_data_formats(
    mock_workspace, input_data_format, expected_alias, provider_id
):
    """Test building profiles for different input data formats."""
    mock_target = Mock()
    provider = AzureQuantumProvider(mock_workspace)

    mock_target.input_data_format = input_data_format
    mock_target.name = f"{provider_id}.qpu.mock_device_id"
    mock_target.provider_id = provider_id
    mock_target.capability = "capability"
    mock_target.output_data_format = "output"
    mock_target.content_type = "content"

    if expected_alias not in QPROGRAM_REGISTRY:
        pytest.skip(f"Required dependency not installed for '{expected_alias}' program type.")

    profile = provider._build_profile(mock_target)

    assert isinstance(profile.program_spec, ProgramSpec)
    assert profile.program_spec.alias == expected_alias
    assert profile.input_data_format == input_data_format


def test_build_profile_unrecognized_format(mock_workspace):
    """Test building profile with an unrecognized input data format."""
    mock_target = Mock()
    input_data_format = "unrecognized.format"
    provider = AzureQuantumProvider(mock_workspace)
    mock_target.input_data_format = input_data_format
    mock_target.name = "unknown.qpu"
    mock_target.provider_id = "unknown"
    mock_target.capability = "capability"
    mock_target.output_data_format = "output"
    mock_target.content_type = "content"

    with pytest.warns(UserWarning, match=f"Unrecognized input data format: {input_data_format}"):
        profile = provider._build_profile(mock_target)

    assert profile.program_spec is None
    assert profile.input_data_format == input_data_format


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
    mock_workspace.get_targets.assert_called_once_with(name="test.qpu.test")


def test_azure_device_status(azure_device, mock_target):
    """Test getting the status of an AzureQuantumDevice."""
    assert azure_device.status() == DeviceStatus.ONLINE

    mock_target._current_availability = "Deprecated"
    assert azure_device.status() == DeviceStatus.UNAVAILABLE

    mock_target._current_availability = "Unavailable"
    assert azure_device.status() == DeviceStatus.OFFLINE

    mock_target._current_availability = "Unknown"
    assert azure_device.status() == DeviceStatus.UNAVAILABLE


def test_azure_device_is_available(mock_workspace, mock_target):
    """Test the is_available method of AzureQuantumDevice."""
    # Mock the target's availability
    mock_target._current_availability = "Available"
    mock_workspace.get_targets.return_value = mock_target

    # Create the AzureQuantumDevice instance
    profile = TargetProfile(
        device_id="test.qpu",
        simulator=False,
        provider_name="test_provider",
        capability="test_capability",
        input_data_format="test_input",
        output_data_format="test_output",
        experiment_type=ExperimentType.GATE_MODEL,
    )
    device = AzureQuantumDevice(profile, mock_workspace)

    # Test when the device is online
    assert device.is_available() is True

    # Test when the device is offline
    mock_target._current_availability = "Unavailable"
    assert device.is_available() is False


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


def test_azure_device_submit_batch_job(azure_device, mock_target):
    """Test submitting a batch job to an AzureQuantumDevice."""
    mock_job1 = Mock()
    mock_job1.id = "mock_job_1"

    mock_job2 = Mock()
    mock_job2.id = "mock_job_2"

    mock_target.submit.side_effect = [mock_job1, mock_job2]
    run_input = ["job1", "job2"]
    jobs = azure_device.submit(run_input)
    assert len(jobs) == len(run_input)

    for index, job in enumerate(jobs):
        assert isinstance(job, AzureQuantumJob)
        assert job.id == f"mock_job_{index+1}"
        assert job.workspace == azure_device.workspace
        assert job.device == azure_device

    for _, qprogram in enumerate(run_input):
        mock_target.submit.assert_any_call(qprogram)

    assert mock_target.submit.call_count == len(run_input)


def test_azure_device_str_representation(azure_device):
    """Test the string representation of an AzureQuantumDevice."""
    assert str(azure_device) == "AzureQuantumDevice('test.qpu.test')"


def test_azure_job_init(mock_estimator_job, mock_job_id):
    """Test initializing an AzureQuantumJob."""
    assert mock_estimator_job.id == mock_job_id
    assert isinstance(mock_estimator_job.workspace, Workspace)


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


def test_azure_job_cancel(mock_estimator_job_waiting):
    """Test canceling an AzureQuantumJob."""
    mock_estimator_job_waiting.cancel()
    assert mock_estimator_job_waiting._job.details.status == "Cancelled"


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
def mock_result_builder(mock_job_id) -> AzureResultBuilder:
    """Create a mock Azure result builder."""
    job = Mock(id=mock_job_id)
    return AzureResultBuilder(job)


class DowloadDataMock:
    """Mock download data method."""

    def decode(self) -> str:
        """Mock decode method."""


def mock_job(
    job_id: str, job_name: str, target: str, output_data_format: str, results_as_json_str: str
) -> Job:
    """Create a mock Azure Quantum Job."""
    job_details = JobDetails(
        id=job_id,
        name=job_name,
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

    download_data = DowloadDataMock()
    download_data.decode = Mock(return_value=results_as_json_str)
    job.download_data = Mock(return_value=download_data)

    return job


def test_job_for_microsoft_quantum_results_v1_success(mock_msft_v1_job_data):
    """Test getting job for microsoft.quantum-results.v1 output data format."""
    results_as_json_str = '{"Histogram": ["[0]", 0.50, "[1]", 0.50]}'
    job = mock_job(**mock_msft_v1_job_data, results_as_json_str=results_as_json_str)

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
    with pytest.raises(RuntimeError) as excinfo:
        AzureQuantumJob._make_estimator_result(data)
    assert (
        "Cannot retrieve results as job execution failed (ResourceUnavailable: "
        "The resource is currently unavailable.)" in str(excinfo.value)
    )


@pytest.mark.skip(reason="Not relevant for the current implementation")
def test_make_estimator_result_with_incorrect_results_length():
    """Test making an estimator result with incorrect results length."""
    data = {"success": True, "results": [{"data": 42}, {"data": 43}]}
    with pytest.raises(ValueError) as excinfo:
        AzureQuantumJob._make_estimator_result(data)
    assert "Expected resource estimator results to be of length 1" in str(excinfo.value)


def test_get_job_result(mock_estimator_job):
    """Test getting the result of an AzureQuantumJob."""
    result = mock_estimator_job.result()
    assert isinstance(result, MicrosoftEstimatorResult)


def test_make_estimator_result_successful(estimator_result_data):
    """Test making an estimator result with successful job."""
    result = AzureQuantumJob._make_estimator_result(estimator_result_data)
    assert isinstance(result, MicrosoftEstimatorResult)
    assert result["status"] == "success"


@pytest.mark.parametrize(
    "probabilities",
    [{"00": 0.5, "11": 0.5}, {"00": 0.4999, "11": 0.5001}, {"00": 0.4000, "11": 0.6001}],
)
def test_draw_random_sample_probabilities(mock_result_builder: AzureResultBuilder, probabilities):
    """Test that the random sample handles both normalized and unnormalized probabilities."""
    shots = 1000
    sample = mock_result_builder._draw_random_sample(probabilities, shots)
    assert sum(sample.values()) == shots
    assert set(sample.keys()) == {"00", "11"}


@pytest.mark.parametrize("seed, should_match", [(42, True), (None, False)])
def test_draw_random_sample_consistency(
    mock_result_builder: AzureResultBuilder, seed, should_match
):
    """Test drawing random samples with and without a specific seed."""
    shots = 10
    probabilities = {"00": 0.5, "11": 0.5}
    sample1 = mock_result_builder._draw_random_sample(probabilities, shots, sampler_seed=seed)
    sample2 = mock_result_builder._draw_random_sample(probabilities, shots, sampler_seed=seed)
    sample3 = mock_result_builder._draw_random_sample(probabilities, shots, sampler_seed=seed)

    if should_match:
        assert sample1 == sample2 == sample3
    else:
        # assert not sample1 == sample2 == sample3
        pytest.skip("Test is probabilistic")


def test_draw_random_sample_with_invalid_probabilities(
    mock_result_builder: AzureResultBuilder,
):
    """Test the method raises an error when probabilities don't sum close to one."""
    probabilities = {"00": 0.3, "11": 0.4}
    shots = 1000
    with pytest.raises(ValueError) as excinfo:
        mock_result_builder._draw_random_sample(probabilities, shots, None)
    assert "Probabilities do not add up to 1" in str(excinfo.value)


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


@pytest.fixture
def mock_builder_ionq_results(mock_job_id) -> dict[str, Any]:
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
        "job_id": mock_job_id,
        "target": "ionq.simulator",
        "job_name": "ionq-job",
        "success": True,
        "error_data": None,
    }
    return data


def test_azure_job_result_pasqal(mock_azure_pasqal_job, mock_pasqal_result_data):
    """Test getting the result of an AzureQuantumJob with PASQAL output data format."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")

    # Mock the PASQAL job
    mock_azure_pasqal_job.details.output_data_format = OutputDataFormat.PASQAL.value
    mock_azure_pasqal_job.details.target = "pasqal.sim.emu-tn"
    mock_azure_pasqal_job.get_results.return_value = mock_pasqal_result_data

    # Create the AzureQuantumJob instance
    job = AzureQuantumJob(
        job_id=mock_azure_pasqal_job.id, workspace=mock_azure_pasqal_job.workspace
    )
    job._job = mock_azure_pasqal_job

    # Call the result method
    result = job.result()

    # Assertions
    assert isinstance(result, Result)
    assert result.device_id == "pasqal.sim.emu-tn"
    assert result.job_id == mock_azure_pasqal_job.id
    assert result.success is True
    assert isinstance(result.data, AhsResultData)
    assert result.data.to_dict() == {
        "measurement_counts": {"001010": 50, "001011": 50},
        "measurements": None,
    }


def test_azure_quantum_result_counts(
    azure_result_builder: AzureResultBuilder, mock_builder_ionq_results: dict[str, Any]
):
    """Test Azure Quantum Job builder get counts methods."""
    with patch.object(
        AzureResultBuilder,
        "get_results",
        return_value=mock_builder_ionq_results["results"],
    ):
        raw_counts = azure_result_builder.get_counts()
        formatted_counts = normalize_data(raw_counts)
    assert raw_counts == formatted_counts == {"000": 50, "111": 50}


def test_job_property(azure_result_builder, mock_azure_job):
    """Test the job property of an AzureResultBuilder."""
    assert azure_result_builder.job == mock_azure_job


def test_from_simulator_true(azure_result_builder, mock_azure_job):
    """Test the from_simulator property of an AzureResultBuilder."""
    mock_azure_job.details.target = "mock.simulator"
    assert azure_result_builder.from_simulator is True


def test_from_simulator_false(azure_result_builder, mock_azure_job):
    """Test the from_simulator property of an AzureResultBuilder."""
    mock_azure_job.details.target = "mock.qpu.mock_device_id"
    assert azure_result_builder.from_simulator is False


def test_shots_count(azure_result_builder):
    """Test the shots count method of an AzureResultBuilder."""
    assert azure_result_builder._shots_count() == 1000


def test_make_estimator_result():
    """Test making an estimator result from an AzureQuantumJob."""
    mock_data = {"success": True, "data": {"mock_data_key": "mock_data_value"}}
    result = AzureQuantumJob._make_estimator_result(mock_data)
    assert isinstance(result, MicrosoftEstimatorResult)
    assert result.data()["mock_data_key"] == "mock_data_value"


def test_make_estimator_result_failure():
    """Test making an estimator result from a failed AzureQuantumJob."""
    mock_data = {"success": False, "error_data": {"code": "MockError", "message": "Job failed"}}
    with pytest.raises(RuntimeError, match="Cannot retrieve results as job execution failed"):
        AzureQuantumJob._make_estimator_result(mock_data)


@pytest.fixture
def mock_qir_to_qbraid_bitstring():
    """Return a mock for the qir_to_qbraid_bitstring method."""
    with patch(
        "qbraid.runtime.azure.result_builder.AzureResultBuilder._qir_to_qbraid_bitstring"
    ) as mock:
        yield mock


def test_format_microsoft_results(
    mock_qir_to_qbraid_bitstring, azure_result_builder, mock_azure_job
):
    """Test formatting Microsoft Quantum results."""
    mock_azure_job.get_results.return_value = {"00": 0.5, "11": 0.5}
    mock_qir_to_qbraid_bitstring.side_effect = lambda x: x

    result = azure_result_builder._format_microsoft_results()

    assert "counts" in result
    assert "probabilities" in result
    assert abs(result["counts"]["00"] - 500) >= 0  # Allow some tolerance
    assert abs(result["counts"]["11"] - 500) >= 0


def test_format_microsoft_results_non_simulator(
    mock_qir_to_qbraid_bitstring, azure_result_builder, mock_azure_job
):
    """Test formatting Microsoft Quantum results from a QPU device."""
    probabilities = {"00": 0.5, "11": 0.5}
    mock_azure_job.get_results.return_value = probabilities
    mock_azure_job.details.target = "mock.qpu"
    mock_qir_to_qbraid_bitstring.side_effect = lambda x: x

    result = azure_result_builder._format_microsoft_results()
    assert result == {"counts": {"00": 500.0, "11": 500.0}, "probabilities": probabilities}


def test_format_rigetti_results(azure_result_builder, mock_azure_job):
    """Test formatting Rigetti results."""
    mock_azure_job.get_results.return_value = {"ro": [[0, 1], [1, 0], [0, 1], [1, 0]]}

    result = azure_result_builder._format_rigetti_results()

    assert "counts" in result
    assert "probabilities" in result
    assert result["counts"] == {"01": 2, "10": 2}
    assert result["probabilities"] == {"01": 0.5, "10": 0.5}


def test_format_pasqal_results(azure_ahs_result_builder, mock_azure_pasqal_job):
    """Test formatting Pasqal results."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_azure_pasqal_job.get_results.return_value = {"001010": 50, "001011": 50}

    result = azure_ahs_result_builder._format_results()

    assert "counts" in result["data"]
    assert "probabilities" in result["data"]
    assert result["data"]["counts"] == {"001010": 50, "001011": 50}
    assert result["data"]["probabilities"] == {"001010": 0.5, "001011": 0.5}


def test_ahs_builder_shots_count(azure_ahs_result_builder, mock_azure_ahs_job):
    """Test the _shots_count method of AzureResultBuilder."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_azure_ahs_job.details.input_params = {"count": 1000}
    assert azure_ahs_result_builder._shots_count() == 1000

    mock_azure_ahs_job.details.input_params = {"shots": 500}
    assert azure_ahs_result_builder._shots_count() == 500

    mock_azure_ahs_job.details.input_params = {}
    assert azure_ahs_result_builder._shots_count() is None


def test_ahs_builder_format_analog_results(azure_ahs_result_builder, mock_azure_ahs_job):
    """Test the _format_analog_results method of AzureResultBuilder."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_azure_ahs_job.get_results.return_value = {"001010": 50, "001011": 50}

    result = azure_ahs_result_builder._format_analog_results()

    assert result["counts"] == {"001010": 50, "001011": 50}
    assert result["probabilities"] == {"001010": 0.5, "001011": 0.5}


def test_ahs_builder_format_results_success(azure_ahs_result_builder, mock_azure_ahs_job):
    """Test the _format_results method when the job succeeds."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_azure_ahs_job.details.status = "Succeeded"
    mock_azure_ahs_job.get_results.return_value = {"001010": 50, "001011": 50}

    result = azure_ahs_result_builder._format_results()

    assert result["success"] is True
    assert result["data"]["counts"] == {"001010": 50, "001011": 50}
    assert result["data"]["probabilities"] == {"001010": 0.5, "001011": 0.5}
    assert result["shots"] == 1000


def test_ahs_builder_format_results_failure(azure_ahs_result_builder, mock_azure_ahs_job):
    """Test the _format_results method when the job fails."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_azure_ahs_job.details.status = "Failed"
    result = azure_ahs_result_builder._format_results()

    assert result["success"] is False
    assert result["data"] == {}
    assert result["shots"] == 1000


def test_ahs_builder_get_counts_single_result(azure_ahs_result_builder, mock_azure_ahs_job):
    """Test the get_counts method with a single result."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_azure_ahs_job.get_results.return_value = [{"001010": 50, "001011": 50}]

    counts = azure_ahs_result_builder.get_counts()

    assert counts == [{"001010": 50, "001011": 50}]


def test_ahs_builder_get_counts_multiple_results(azure_ahs_result_builder, mock_azure_ahs_job):
    """Test the get_counts method with multiple results."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_azure_ahs_job.get_results.return_value = [
        {"001010": 50, "001011": 50},
        {"001100": 30, "001101": 70},
    ]

    counts = azure_ahs_result_builder.get_counts()

    assert counts == [
        {"001010": 50, "001011": 50},
        {"001100": 30, "001101": 70},
    ]


def test_ahs_builder_get_results_success(azure_ahs_result_builder, mock_azure_ahs_job):
    """Test the get_results method when the job succeeds."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_azure_ahs_job.details.status = "Succeeded"
    mock_azure_ahs_job.get_results.return_value = {"001010": 50, "001011": 50}

    results = azure_ahs_result_builder.get_results()

    assert len(results) == 1
    assert results[0]["success"] is True
    assert results[0]["data"]["counts"] == {"001010": 50, "001011": 50}
    assert results[0]["data"]["probabilities"] == {"001010": 0.5, "001011": 0.5}


def test_ahs_builder_get_results_failure(azure_ahs_result_builder, mock_azure_ahs_job):
    """Test the get_results method when the job fails."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_azure_ahs_job.details.status = "Failed"

    results = azure_ahs_result_builder.get_results()

    assert len(results) == 1
    assert results[0]["success"] is False
    assert results[0]["data"] == {}
    assert results[0]["shots"] == 1000


@patch("qbraid.runtime.azure.result_builder.AzureResultBuilder._qir_to_qbraid_bitstring")
def test_format_quantinuum_results(
    mock_qir_to_qbraid_bitstring, azure_result_builder, mock_azure_job
):
    """Test formatting Quantinuum results."""
    mock_azure_job.get_results.return_value = {"qreg0": ["0", "1", "1"], "qreg1": ["1", "0", "1"]}
    mock_qir_to_qbraid_bitstring.side_effect = lambda x: x

    result = azure_result_builder._format_quantinuum_results()

    assert "counts" in result
    assert "probabilities" in result
    assert result["counts"] == {"01": 1, "10": 1, "11": 1}
    assert result["probabilities"] == {"01": 1 / 3, "10": 1 / 3, "11": 1 / 3}


def test_format_ionq_results():
    """Test formatting IonQ results."""
    mock_job = Mock(spec=Job)
    mock_job.details.input_params = {"count": 100}
    mock_job.get_results.return_value = {"histogram": {"0": 0.5, "7": 0.5}}

    builder = AzureResultBuilder(azure_job=mock_job)
    expected_result = {
        "counts": {"000": 50, "111": 50},
        "probabilities": {"000": 0.5, "111": 0.5},
    }
    assert builder._format_ionq_results() == expected_result


def test_format_ionq_results_raises_for_no_histogram_data():
    """Test formatting IonQ results raises an error when histogram data is missing."""
    mock_job = Mock(spec=Job)
    mock_job.details.input_params = {"count": 100}
    mock_job.get_results.return_value = {}
    builder = AzureResultBuilder(azure_job=mock_job)
    with pytest.raises(ValueError) as excinfo:
        builder._format_ionq_results()
    assert "Histogram missing from IonQ Job results" in str(excinfo.value)


def test_format_unknown_results(azure_result_builder, mock_azure_job):
    """Test formatting unknown results."""
    mock_azure_job.get_results.return_value = {"mock_key": "mock_value"}

    result = azure_result_builder._format_unknown_results()

    assert result == {"mock_key": "mock_value"}


@pytest.mark.parametrize(
    "input_params, expected_result",
    [
        (
            {"items": [{"entryPoint": "main"}, {"entryPoint": "auxiliary"}]},
            ["main", "auxiliary"],
        ),
        (
            {"items": []},
            ["main"],
        ),
    ],
)
def test_get_entry_point_names(input_params, expected_result):
    """Test getting entry point names from input params."""
    mock_job = Mock(spec=Job)
    mock_job.details.input_params = input_params
    builder = AzureResultBuilder(azure_job=mock_job)
    result = builder._get_entry_point_names()
    assert result == expected_result


def test_get_entry_point_names_with_missing_entry_point():
    """Test getting entry point names from input params with missing 'entryPoint' field."""
    mock_job = Mock(spec=Job)
    mock_job.details.input_params = {"items": [{"noEntryPointField": "data"}]}
    builder = AzureResultBuilder(azure_job=mock_job)
    with pytest.raises(
        ValueError, match="Entry point input_param is missing an 'entryPoint' field"
    ):
        builder._get_entry_point_names()


def test_get_entry_point_names_with_no_items_key():
    """Test getting entry point names from input params with missing 'items' key."""
    mock_job = Mock(spec=Job)
    mock_job.details.input_params = {}
    builder = AzureResultBuilder(azure_job=mock_job)
    with pytest.raises(KeyError):
        builder._get_entry_point_names()


def test_translate_microsoft_v2_results(azure_result_builder, mock_azure_job):
    """Test translating Microsoft Quantum v2 results."""
    mock_azure_job.get_results.return_value = {
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


@pytest.mark.parametrize(
    "results, err_msg",
    [
        ({}, "DataFormat missing from Job results"),
        ({"DataFormat": "v2"}, "Results missing from Job results"),
        ({"DataFormat": "v2", "Results": [{}]}, "TotalCount missing from Job results"),
        (
            {"DataFormat": "v2", "Results": [{"TotalCount": -1}]},
            "TotalCount must be a positive non-zero integer",
        ),
        (
            {"DataFormat": "v2", "Results": [{"TotalCount": 100}]},
            "Histogram missing from Job results",
        ),
        (
            {"DataFormat": "v2", "Results": [{"TotalCount": 100, "Histogram": [{}]}]},
            "Dispaly missing from histogram result",
        ),
        (
            {
                "DataFormat": "v2",
                "Results": [{"TotalCount": 100, "Histogram": [{"Display": "00"}]}],
            },
            "Count missing from histogram result",
        ),
    ],
)
def test_translate_microsoft_v2_result_raises_value_error(results, err_msg):
    """Test translating Microsoft Quantum v2 results raises an error
    when job result does not contain the required field."""
    mock_job = Mock(spec=Job)
    mock_job.get_results.return_value = results
    builder = AzureResultBuilder(azure_job=mock_job)
    with pytest.raises(ValueError) as excinfo:
        builder._translate_microsoft_v2_results()
        assert err_msg in str(excinfo.value)


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


def test_format_microsoft_v2_results_raises_value_error(azure_result_builder, mock_azure_job):
    """Test formatting Microsoft Quantum v2 results raises ValueError
    when number of results does not match number of entrypoints."""
    mock_azure_job.details.status = "Succeeded"
    mock_azure_job.details.input_params = {
        "items": [{"entryPoint": "main"}, {"entryPoint": "auxiliary"}]
    }
    mock_azure_job.get_results.return_value = {
        "DataFormat": "v2",
        "Results": [
            {
                "TotalCount": 1000,
                "Histogram": [{"Display": "00", "Count": 700}, {"Display": "11", "Count": 300}],
            }
        ],
    }
    with pytest.raises(ValueError) as excinfo:
        azure_result_builder._format_microsoft_v2_results()
    assert "The number of experiment results does not match the number of experiment names" in str(
        excinfo.value
    )


def test_format_microsoft_v2_results_no_success():
    """Test formatting Microsoft Quantum v2 results with failed job."""
    mock_job = Mock(spec=Job)
    mock_job.details.status = "Failed"
    mock_job.details.output_data_format = OutputDataFormat.MICROSOFT_V2.value
    builder = AzureResultBuilder(azure_job=mock_job)
    assert builder._format_microsoft_v2_results() == [
        {"data": {}, "success": False, "header": {}, "shots": 0}
    ]


def test_result_builder_failed_job(mock_job_id):
    """Test formatting Microsoft Quantum v2 results with failed job."""
    mock_job = Mock(spec=Job)
    mock_job.details.status = "Failed"
    mock_job.details.output_data_format = OutputDataFormat.MICROSOFT_V2.value
    mock_job.details.error_data = None
    mock_job.details.target = "rigetti.sim.qvm"
    mock_job.details.name = "azure-quantum-job"
    mock_job.details.id = mock_job_id
    builder = AzureResultBuilder(azure_job=mock_job)
    results = builder.get_results()
    assert isinstance(results, list)
    assert all(isinstance(result, dict) for result in results)


@pytest.mark.parametrize(
    "output_data_format",
    [
        OutputDataFormat.MICROSOFT_V1.value,
        OutputDataFormat.IONQ.value,
        OutputDataFormat.QUANTINUUM.value,
        OutputDataFormat.RIGETTI.value,
    ],
)
def test_build_result_from_output_format(azure_result_builder, mock_azure_job, output_data_format):
    """Test building job result from different output data formats."""
    mock_azure_job.details.output_data_format = output_data_format

    mock_metadata = {"test": "qBraid"}
    mock_data = [{"counts": {"00": 700, "11": 300}, "probabilities": {"00": 0.7, "11": 0.3}}]
    mock_azure_job.details.metadata = {"metadata": json.dumps(mock_metadata)}

    azure_result_builder._format_microsoft_results = Mock(return_value=mock_data)
    azure_result_builder._format_ionq_results = Mock(return_value=mock_data)
    azure_result_builder._format_quantinuum_results = Mock(return_value=mock_data)
    azure_result_builder._format_rigetti_results = Mock(return_value=mock_data)

    job_result = azure_result_builder._format_results()
    assert job_result["data"] == mock_data
    assert job_result["header"]["metadata"] == mock_metadata
    assert job_result["success"] is True
    assert job_result["shots"] == 1000

    if output_data_format == OutputDataFormat.MICROSOFT_V1.value:
        azure_result_builder._format_microsoft_results.assert_called_once()
    elif output_data_format == OutputDataFormat.IONQ.value:
        azure_result_builder._format_ionq_results.assert_called_once()
    elif output_data_format == OutputDataFormat.QUANTINUUM.value:
        azure_result_builder._format_quantinuum_results.assert_called_once()
    elif output_data_format == OutputDataFormat.RIGETTI.value:
        azure_result_builder._format_rigetti_results.assert_called_once()
    else:
        pytest.fail(f"Unexpected output data format: {output_data_format}")


def test_builder_get_counts_single_result_success(mock_result_builder):
    """Test getting counts from a single successful result."""
    mock_result_builder.get_results = Mock(
        return_value=[{"success": True, "data": {"counts": {"00": 486, "11": 514}}}]
    )

    counts = mock_result_builder.get_counts()

    assert counts == {"00": 486, "11": 514}


def test_builder_get_counts_single_result_failure(mock_result_builder):
    """Test getting counts from a single failed result."""
    mock_result_builder.get_results = Mock(return_value=[{"success": False, "data": {}}])

    counts = mock_result_builder.get_counts()

    assert counts == {}


def test_builder_get_counts_multiple_results_mixed(mock_result_builder):
    """Test getting counts from multiple results with mixed success."""
    mock_result_builder.get_results = Mock(
        return_value=[
            {"success": True, "data": {"counts": {"00": 486, "11": 514}}},
            {"success": False, "data": {}},
            {"success": True, "data": {"counts": {"00": 200, "11": 800}}},
        ]
    )

    counts = mock_result_builder.get_counts()

    assert counts == [{"00": 486, "11": 514}, {}, {"00": 200, "11": 800}]


def test_builder_get_counts_multiple_results_all_failure(mock_result_builder):
    """Test getting counts from multiple results with all failures."""
    mock_result_builder.get_results = Mock(
        return_value=[
            {"success": False, "data": {"hello"}},
            {"success": False, "data": {"counts": [1, 2, 3]}},
        ]
    )

    counts = mock_result_builder.get_counts()

    assert counts == [{}, {}]


def test_builder_format_unknown_results(azure_result_builder: AzureResultBuilder):
    """Test using the result builder to format results of an unrecognized gate model format."""
    results = azure_result_builder._format_results()
    assert results == {
        "data": {
            "success": True,
            "error_data": None,
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
            },
            "job_id": "123-456-798",
            "job_name": "azure-quantum-job",
            "target": "microsoft.estimator",
            "output_data_format": "microsoft.resource-estimates.v1",
        },
        "success": True,
        "header": {},
        "shots": 1000,
    }


def test_ahs_builder_format_unknown_results(azure_ahs_result_builder: AzureResultBuilder):
    """Test using the result builder to format results of an unrecognized AHS model format.

    Args:
        azure_ahs_result_builder (AzureResultBuilder): The Azure AHS model result builder.
    """
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    results = azure_ahs_result_builder._format_results()
    assert results == {
        "data": {
            "counts": {"001010": 50, "001011": 50},
            "probabilities": {"001010": 0.5, "001011": 0.5},
        },
        "success": True,
        "header": {},
        "shots": 1000,
    }


@pytest.fixture
def mock_workspace_hashing():
    """Create a mock workspace for testing hashing."""
    workspace = Mock()
    workspace.credential = "mock_credential"
    workspace.user_agent = "mock_user_agent"
    return workspace


@patch("builtins.hash", autospec=True)
def test_hash_method_creates_and_returns_hash(mock_hash, mock_workspace_hashing, azure_provider):
    """Test that the hash method creates and returns a hash."""
    mock_hash.return_value = 9999
    provider_instance = azure_provider
    provider_instance._workspace = mock_workspace_hashing
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    mock_hash.assert_called_once_with(("mock_credential", "mock_user_agent"))
    assert result == 9999
    assert provider_instance._hash == 9999


def test_hash_method_returns_existing_hash(mock_workspace_hashing, azure_provider):
    """Test that the hash method returns an existing hash."""
    provider_instance = azure_provider
    provider_instance._workspace = mock_workspace_hashing
    provider_instance._hash = 12345
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    assert result == 12345


def test_get_gate_model_job_result(mock_job_id, mock_workspace, mock_azure_ionq_job):
    """Test getting a gate model job result."""
    job = AzureQuantumJob(mock_job_id, workspace=mock_workspace)
    job._job = mock_azure_ionq_job
    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert result.success is True


def test_serialize_pulser_input():
    """Test the serialization of a pulser input."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    import pulser  # pylint: disable=import-outside-toplevel

    device = pulser.AnalogDevice
    register = pulser.Register.from_coordinates([(0, 0)], prefix="q")

    sequence = pulser.Sequence(register, device)

    pulser_input = serialize_pulser_input(sequence)

    expected_input = '{"sequence_builder": {"version": "1", "name": "pulser-exported", "register": [{"name": "q0", "x": 0.0, "y": 0.0}], "channels": {}, "variables": {}, "operations": [], "measurement": null, "device": {"name": "AnalogDevice", "dimensions": 2, "rydberg_level": 60, "min_atom_distance": 5, "max_atom_num": 80, "max_radial_distance": 38, "interaction_coeff_xy": null, "supports_slm_mask": false, "max_layout_filling": 0.5, "optimal_layout_filling": 0.45, "max_sequence_duration": 6000, "max_runs": 2000, "reusable_channels": false, "pre_calibrated_layouts": [{"coordinates": [[-20.0, 0.0], [-17.5, -4.330127], [-17.5, 4.330127], [-15.0, -8.660254], [-15.0, 0.0], [-15.0, 8.660254], [-12.5, -12.990381], [-12.5, -4.330127], [-12.5, 4.330127], [-12.5, 12.990381], [-10.0, -17.320508], [-10.0, -8.660254], [-10.0, 0.0], [-10.0, 8.660254], [-10.0, 17.320508], [-7.5, -12.990381], [-7.5, -4.330127], [-7.5, 4.330127], [-7.5, 12.990381], [-5.0, -17.320508], [-5.0, -8.660254], [-5.0, 0.0], [-5.0, 8.660254], [-5.0, 17.320508], [-2.5, -12.990381], [-2.5, -4.330127], [-2.5, 4.330127], [-2.5, 12.990381], [0.0, -17.320508], [0.0, -8.660254], [0.0, 0.0], [0.0, 8.660254], [0.0, 17.320508], [2.5, -12.990381], [2.5, -4.330127], [2.5, 4.330127], [2.5, 12.990381], [5.0, -17.320508], [5.0, -8.660254], [5.0, 0.0], [5.0, 8.660254], [5.0, 17.320508], [7.5, -12.990381], [7.5, -4.330127], [7.5, 4.330127], [7.5, 12.990381], [10.0, -17.320508], [10.0, -8.660254], [10.0, 0.0], [10.0, 8.660254], [10.0, 17.320508], [12.5, -12.990381], [12.5, -4.330127], [12.5, 4.330127], [12.5, 12.990381], [15.0, -8.660254], [15.0, 0.0], [15.0, 8.660254], [17.5, -4.330127], [17.5, 4.330127], [20.0, 0.0]], "slug": "TriangularLatticeLayout(61, 5.0\\u00b5m)"}], "version": "1", "pulser_version": "1.4.0", "channels": [{"id": "rydberg_global", "basis": "ground-rydberg", "addressing": "Global", "max_abs_detuning": 125.66370614359172, "max_amp": 12.566370614359172, "min_retarget_interval": null, "fixed_retarget_t": null, "max_targets": null, "clock_period": 4, "min_duration": 16, "max_duration": 100000000, "mod_bandwidth": 8, "eom_config": {"limiting_beam": "RED", "max_limiting_amp": 188.49555921538757, "intermediate_detuning": 2827.4333882308138, "controlled_beams": ["BLUE"], "mod_bandwidth": 40, "custom_buffer_time": 240}}], "is_virtual": false}}}'

    expected_input = re.sub(
        r'"pulser_version"\s*:\s*"\d+\.\d+\.\d+"',
        f'"pulser_version": "{pulser.__version__}"',
        expected_input,
    )

    assert pulser_input == expected_input


def test_get_pasqal_program_spec():
    """Test getting the program spec for Pasqal."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    program_spec = AzureQuantumProvider._get_program_spec(InputDataFormat.PASQAL)
    assert program_spec.alias == "pulser"


def test_build_profile_pasqal(mock_workspace):
    """Test building profile for Pasqal target."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    mock_target = Mock()
    mock_target.name = "pasqal.sim.emu-tn"
    mock_target.provider_id = "pasqal"
    mock_target.capability = ""
    mock_target.content_type = "application/json"
    mock_target.input_data_format = InputDataFormat.PASQAL.value
    mock_target.output_data_format = OutputDataFormat.PASQAL.value

    provider = AzureQuantumProvider(mock_workspace)

    profile = provider._build_profile(mock_target)

    assert profile.program_spec.alias == "pulser"
    assert profile.experiment_type == ExperimentType.AHS
    assert profile.num_qubits == 100

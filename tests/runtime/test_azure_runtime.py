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
Module defining Azure Quantum device class for all devices managed by Azure Quantum.

"""

from unittest.mock import Mock

import numpy as np
import pytest
from azure.identity import ClientSecretCredential
from azure.quantum import Workspace
from azure.quantum.target import Target

from qbraid.runtime.azure.device import AzureQuantumDevice
from qbraid.runtime.azure.job import AzureQuantumJob, AzureQuantumResult
from qbraid.runtime.azure.provider import AzureQuantumProvider
from qbraid.runtime.enums import DeviceActionType, DeviceStatus, DeviceType, JobStatus
from qbraid.runtime.exceptions import JobStateError, ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile


@pytest.fixture
def mock_workspace():
    """Return a mock Azure Quantum workspace."""
    return Mock(spec=Workspace)


@pytest.fixture
def mock_workspace_credential_free():
    """Return a mock Azure Quantum workspace without a credential."""
    return Workspace(
        subscription_id="something",
        resource_group="something",
        name="something",
        location="something",
        # credential=credential,
    )


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
        device_type=DeviceType.QPU,
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
    mock_job.id = "test_job_id"
    mock_job.details.status = "Waiting"

    mock_job_cancelled = Mock()
    mock_job_cancelled.id = "test_job_id"
    mock_job_cancelled.details.status = "Cancelled"

    mock_workspace.get_job.return_value = mock_job
    mock_workspace.cancel_job.return_value = mock_job_cancelled

    return AzureQuantumJob(job_id="test_job_id", workspace=mock_workspace)


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


def test_init_without_credential(mock_workspace_credential_free):
    """Test initializing an AzureQuantumProvider without a credential."""
    with pytest.warns(Warning):
        AzureQuantumProvider(mock_workspace_credential_free)


def test_azure_provider_workspace_property(azure_provider, mock_workspace):
    """Test the workspace property of an AzureQuantumProvider."""
    assert azure_provider.workspace == mock_workspace


def test_build_profile(azure_provider, mock_target):
    """Test building a profile for an AzureQuantumProvider."""
    profile = azure_provider._build_profile(mock_target)

    assert isinstance(profile, TargetProfile)
    assert profile.action_type == "OpenQASM"


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
    mock_job.id = "test_job_id"
    mock_target.submit.return_value = mock_job

    run_input = "test_input"
    job = azure_device.submit(run_input)

    assert isinstance(job, AzureQuantumJob)
    assert job.id == "test_job_id"
    assert job.workspace == azure_device.workspace
    assert job.device == azure_device

    mock_target.submit.assert_called_once_with(run_input)


def test_azure_device_submit_batch_job(azure_device):
    """Test submitting a batch job to an AzureQuantumDevice."""
    with pytest.raises(ValueError):
        azure_device.submit(["job1", "job2"], name="batch_job")


def test_azure_job_init(mock_azure_job):
    """Test initializing an AzureQuantumJob."""
    assert mock_azure_job.id == "test_job_id"
    assert isinstance(mock_azure_job.workspace, Workspace)


def test_azure_job_status(mock_azure_job):
    """Test getting the status of an AzureQuantumJob."""
    assert mock_azure_job.status() == JobStatus.QUEUED

    mock_azure_job._job.details.status = "Executing"
    assert mock_azure_job.status() == JobStatus.RUNNING

    mock_azure_job._job.details.status = "Failed"
    assert mock_azure_job.status() == JobStatus.FAILED

    mock_azure_job._job.details.status = "Cancelled"
    assert mock_azure_job.status() == JobStatus.CANCELLED

    mock_azure_job._job.details.status = "Succeeded"
    assert mock_azure_job.status() == JobStatus.COMPLETED

    mock_azure_job._job.details.status = "Unknown"
    assert mock_azure_job.status() == JobStatus.UNKNOWN


def test_azure_job_result(mock_azure_job):
    """Test getting the result of an AzureQuantumJob."""
    mock_azure_job._job.get_results.return_value = {
        "meas": ["00", "01", "00", "10", "00", "01"],
        "other_data": [1, 2, 3],
    }
    result = mock_azure_job.result()
    assert isinstance(result, AzureQuantumResult)
    assert np.array_equal(result.measurements(), np.array(["00", "01", "00", "10", "00", "01"]))


def test_azure_job_result_error(mock_azure_job):
    """Test getting the result of an AzureQuantumJob in a non-terminal state."""
    mock_azure_job._job.get_results.return_value = {"no_meas": [1, 2, 3]}
    with pytest.raises(RuntimeError):
        mock_azure_job.result()


def test_azure_job_cancel(mock_azure_job):
    """Test canceling an AzureQuantumJob."""
    mock_azure_job.cancel()
    assert mock_azure_job._job.details.status == "Cancelled"


def test_azure_job_cancel_terminal_state(mock_azure_job):
    """Test canceling an AzureQuantumJob in a terminal state."""
    mock_azure_job._job.details.status = "Succeeded"
    with pytest.raises(JobStateError):
        mock_azure_job.cancel()


def test_azure_result_init(azure_result):
    """Test initializing an AzureQuantumResult."""
    assert isinstance(azure_result, AzureQuantumResult)
    assert azure_result._result == {
        "meas": ["00", "01", "00", "10", "00", "01"],
        "other_data": [1, 2, 3],
    }


def test_azure_result_measurements(azure_result):
    """Test getting measurements from an AzureQuantumResult."""
    measurements = azure_result.measurements()
    assert isinstance(measurements, np.ndarray)
    assert np.array_equal(measurements, np.array(["00", "01", "00", "10", "00", "01"]))


def test_azure_result_measurement_counts(azure_result):
    """Test getting measurement counts from an AzureQuantumResult."""
    counts = azure_result.measurement_counts()
    assert counts == {"00": 3, "01": 2, "10": 1}


def test_azure_result_raw_counts(azure_result):
    """Test getting raw counts from an AzureQuantumResult."""
    raw_counts = list(azure_result.raw_counts())
    assert raw_counts == [["00", "01", "00", "10", "00", "01"], [1, 2, 3]]

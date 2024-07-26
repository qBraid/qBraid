# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
#
# pylint:disable=redefined-outer-name
"""
Module defining Azure Quantum device class for all devices managed by Azure Quantum.

"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from azure.quantum import Workspace
from azure.quantum.job import Job

from qbraid.runtime.azure.client import AzureClient
from qbraid.runtime.azure.device import AzureQuantumDevice
from qbraid.runtime.azure.job import AzureJob
from qbraid.runtime.azure.provider import AzureQuantumProvider
from qbraid.runtime.azure.result import AzureResult
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.exceptions import ResourceNotFoundError

# ------------------------------------------------------------
# AZURE RESULT TESTS
# ------------------------------------------------------------


def test_azure_result_initialization():
    """Test the initialization of the AzureResult class."""
    result_data = {"key1": "value1", "key2": "value2"}
    azure_result = AzureResult(result_data)
    assert azure_result.data == result_data


def test_azure_result_measurements():
    """Test the measurements property of the AzureResult class."""
    result_data = {"key1": "value1", "key2": "value2"}
    azure_result = AzureResult(result_data)
    assert list(azure_result.measurements) == list(result_data.keys())


def test_azure_result_raw_counts():
    """Test the raw_counts property of the AzureResult class."""
    result_data = {"key1": "value1", "key2": "value2"}
    azure_result = AzureResult(result_data)
    assert list(azure_result.raw_counts) == list(result_data.values())


# ------------------------------------------------------------
# AZURE PROVIDER TESTS
# ------------------------------------------------------------


@pytest.fixture
def mock_provider_client():
    """Fixture for a mock AzureClient object."""
    client = Mock(spec=AzureClient)
    client.get_devices.return_value = {"device1.qpu": {}, "device2.simulator": {}}
    client.get_device.return_value = {"name": "device1.qpu"}
    return client


def test_azure_quantum_provider_initialization(mock_provider_client):
    """Test the initialization of the AzureQuantumProvider class."""
    provider = AzureQuantumProvider(mock_provider_client)
    assert provider.client == mock_provider_client


def test_azure_quantum_provider_get_devices(mock_provider_client):
    """Test the get_devices method of the AzureQuantumProvider class."""
    provider = AzureQuantumProvider(mock_provider_client)
    devices = provider.get_devices()
    assert len(devices) == 2
    assert all(isinstance(device, AzureQuantumDevice) for device in devices)


def test_azure_quantum_provider_get_device(mock_provider_client):
    """Test the get_device method of the AzureQuantumProvider class."""
    provider = AzureQuantumProvider(mock_provider_client)
    device = provider.get_device("device1.qpu")
    assert isinstance(device, AzureQuantumDevice)


def test_azure_quantum_provider_get_device_not_found(mock_provider_client):
    """Test the get_device method of the AzureQuantumProvider class when the device is not found."""
    mock_provider_client.get_device.return_value = None
    provider = AzureQuantumProvider(mock_provider_client)
    with pytest.raises(ValueError, match="Device device1.qpu not found."):
        provider.get_device("device1.qpu")


# ------------------------------------------------------------
# AZURE JOB TESTS
# ------------------------------------------------------------


@pytest.fixture
def mock_job_client():
    """Fixture for a mock AzureClient object."""
    client = Mock(spec=AzureClient)
    client.get_job.return_value = Mock(details=Mock(status="Succeeded"))
    client.cancel_job.return_value = None
    client.get_job_results.return_value = {"key": "value"}
    return client


def test_azure_job_initialization(mock_job_client):
    """Test the initialization of the AzureJob class."""
    job_id = "job1"
    job = AzureJob(job_id=job_id, client=mock_job_client)
    assert job.client == mock_job_client
    assert job.id == job_id


def test_azure_job_status(mock_job_client):
    """Test the status method of the AzureJob class."""
    mock_job_client.get_job.return_value.details.status = "Succeeded"
    job = AzureJob(job_id="job1", client=mock_job_client)
    assert job.status() == JobStatus.COMPLETED

    mock_job_client.get_job.return_value.details.status = "Waiting"
    assert job.status() == JobStatus.QUEUED

    mock_job_client.get_job.return_value.details.status = "Executing"
    assert job.status() == JobStatus.RUNNING

    mock_job_client.get_job.return_value.details.status = "Failed"
    assert job.status() == JobStatus.FAILED

    mock_job_client.get_job.return_value.details.status = "Cancelled"
    assert job.status() == JobStatus.CANCELLED

    mock_job_client.get_job.return_value.details.status = "UnknownStatus"
    assert job.status() == JobStatus.UNKNOWN


def test_azure_job_cancel(mock_job_client):
    """Test the cancel method of the AzureJob class."""
    job = AzureJob(job_id="job1", client=mock_job_client)
    job.cancel()
    mock_job_client.cancel_job.assert_called_once_with(job.azure_job)


def test_azure_job_result(mock_job_client):
    """Test the result method of the AzureJob class."""
    job = AzureJob(job_id="job1", client=mock_job_client)
    result = job.result()
    assert isinstance(result, AzureResult)
    assert result.data == {"key": "value"}


# ------------------------------------------------------------
# AZURE QUANTUM DEVICE TESTS
# ------------------------------------------------------------


@pytest.fixture
def mock_device_client():
    """Fixture for a mock AzureClient object."""
    client = Mock()
    client.get_device = MagicMock()
    client.submit_job = MagicMock()
    return client


@pytest.fixture
def azure_quantum_device(mock_device_client):
    """Fixture for an AzureQuantumDevice object."""
    profile = Mock()  # Mocking TargetProfile or any other profile
    device = AzureQuantumDevice(profile=profile, client=mock_device_client)
    # Mock the device's id to avoid using a mock object for it
    device._id = "device1"
    return device


def test_azure_quantum_device_initialization(mock_device_client):
    """Test the initialization of the AzureQuantumDevice class."""
    profile = Mock()
    device = AzureQuantumDevice(profile=profile, client=mock_device_client)
    assert device.client == mock_device_client
    assert device.profile == profile


def test_azure_quantum_device_status_available(azure_quantum_device, mock_device_client):
    """Test the status method of the AzureQuantumDevice class when the device is available."""
    mock_device_client.get_device.return_value = {"_current_availability": "Available"}
    assert azure_quantum_device.status() == DeviceStatus.ONLINE


def test_azure_quantum_device_status_deprecated(azure_quantum_device, mock_device_client):
    """Test the status method of the AzureQuantumDevice class when the device is deprecated."""
    mock_device_client.get_device.return_value = {"_current_availability": "Deprecated"}
    assert azure_quantum_device.status() == DeviceStatus.UNAVAILABLE


def test_azure_quantum_device_status_unavailable(azure_quantum_device, mock_device_client):
    """Test the status method of the AzureQuantumDevice class when the device is unavailable."""
    mock_device_client.get_device.return_value = {"_current_availability": "Unavailable"}
    assert azure_quantum_device.status() == DeviceStatus.OFFLINE


def test_azure_quantum_device_status_unknown(azure_quantum_device, mock_device_client):
    """Test the status method of the AzureQuantumDevice class when the device status is unknown."""
    mock_device_client.get_device.return_value = {"_current_availability": "Unknown"}
    assert azure_quantum_device.status() == DeviceStatus.UNAVAILABLE


def test_azure_quantum_device_submit_job(azure_quantum_device, mock_device_client):
    """Test the submit method of the AzureQuantumDevice class."""
    job = Mock()
    job.id = "job1"  # Set job id attribute directly
    mock_device_client.submit_job.return_value = job
    program = "some_program"
    job_name = "test_job"
    shots = 200

    result_job = azure_quantum_device.submit(program=program, job_name=job_name, shots=shots)

    assert isinstance(result_job, AzureJob)
    assert result_job.id == "job1"
    assert result_job.client == mock_device_client
    assert result_job.device == azure_quantum_device


def test_azure_quantum_device_submit_job_batch_error(azure_quantum_device):
    """Test the submit method of the AzureQuantumDevice class when a batch program is provided."""
    with pytest.raises(ValueError, match="Batch jobs"):
        azure_quantum_device.submit(program=["batch_program"], job_name="test_job")


# ------------------------------------------------------------
# AZURE CLIENT TESTS
# ------------------------------------------------------------


@pytest.fixture
def mock_workspace():
    """Fixture for a mock Azure Quantum workspace object."""
    return Mock(spec=Workspace)


@pytest.fixture
def azure_client(mock_workspace):
    """Fixture for an AzureClient object."""
    return AzureClient(mock_workspace)


def test_init(azure_client, mock_workspace):
    """Test the initialization of the AzureClient class."""
    assert azure_client.workspace == mock_workspace


def test_from_workspace():
    """Test the from_workspace method of the AzureClient class."""
    mock_workspace = Mock(spec=Workspace)
    mock_credential = Mock()

    client = AzureClient.from_workspace(mock_workspace, mock_credential)
    assert isinstance(client, AzureClient)
    assert client.workspace == mock_workspace


def test_get_devices(azure_client):
    """Test the get_devices method of the AzureClient class."""
    mock_device1 = Mock(name="device1", provider_id="provider1", _current_availability="Available")
    mock_device2 = Mock(name="device2", provider_id="provider2", _current_availability="Offline")
    azure_client.workspace.get_targets.return_value = [mock_device1, mock_device2]

    devices = azure_client.get_devices()
    assert len(devices) == 2

    filtered_devices = azure_client.get_devices(providers=["provider1"], statuses=["Available"])
    assert len(filtered_devices) == 1


def test_get_device(azure_client):
    """Test the get_device method of the AzureClient class."""
    mock_device = {
        "input_data_format": "mock_format",
        "output_data_format": "mock_format",
        "capability": "mock_capability",
        "provider_id": "mock_provider",
        "content_type": "mock_content_type",
        "_average_queue_time": "mock_queue_time",
        "_current_availability": "Available",
    }

    # Patch get_devices to return a dictionary
    with patch.object(azure_client, "get_devices", return_value={"test_device": mock_device}):
        # Test successful retrieval
        device = azure_client.get_device("test_device")
        assert device == {**mock_device, "name": "test_device"}

        # Test device not found
        with pytest.raises(ResourceNotFoundError):
            azure_client.get_device("non_existent_device")


def test_submit_job(azure_client):
    """Test the submit_job method of the AzureClient class."""
    mock_target = Mock()
    mock_job = Mock(spec=Job)
    azure_client.workspace.get_targets.return_value = mock_target
    mock_target.submit.return_value = mock_job

    data_dict = {
        "device_name": "test_device",
        "program": "test_program",
        "job_name": "test_job",
        "shots": 1000,
    }

    job = azure_client.submit_job(data_dict)
    assert job == mock_job
    mock_target.submit.assert_called_once_with(
        input_data="test_program", name="test_job", shots=1000
    )


def test_get_job(azure_client):
    """Test the get_job method of the AzureClient class."""
    mock_job = Mock(spec=Job)
    azure_client.workspace.get_job.return_value = mock_job

    job = azure_client.get_job("test_job_id")
    assert job == mock_job
    azure_client.workspace.get_job.assert_called_once_with("test_job_id")


def test_get_job_results(azure_client):
    """Test the get_job_results method of the AzureClient class."""
    mock_job = Mock(spec=Job)
    mock_results = {"results": "test_results"}
    mock_job.get_results.return_value = mock_results

    results = azure_client.get_job_results(mock_job)
    assert results == mock_results
    mock_job.get_results.assert_called_once()


def test_cancel_job(azure_client):
    """Test the cancel_job method of the AzureClient class."""
    mock_job = Mock(spec=Job)
    azure_client.cancel_job(mock_job)
    azure_client.workspace.cancel_job.assert_called_once_with(mock_job)

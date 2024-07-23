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
# pylint: disable=line-too-long

"""
Unit tests for Azure Session, Provider, Device, and Job classes.

"""
import re
from typing import Any
from unittest.mock import Mock, patch
from uuid import uuid4

import openqasm3
import pytest
from azure.storage.blob import BlobServiceClient, ContentSettings
from qbraid_core._import import LazyLoader
from qbraid_core.sessions import Session

from qbraid.runtime.azure.device import AzureQuantumDevice
from qbraid.runtime.azure.job import AzureJob
from qbraid.runtime.azure.provider import AzureQuantumProvider
from qbraid.runtime.azure.session import AzureSession
from qbraid.runtime.enums import DeviceStatus, DeviceType, JobStatus
from qbraid.runtime.profile import ProgramSpec, TargetProfile

pyquil = LazyLoader("pyquil", globals(), "pyquil")
openqasm3 = LazyLoader("openqasm3", globals(), "openqasm3")

# ---------------ALL FIXTURES---------------------
# Fixtures for all tests.
# -------------------------------------------------


@pytest.fixture
def auth_data():
    """Return a dictionary with fake authentication data."""
    return {
        "client_id": "fake_client_id",
        "client_secret": "fake_client_secret",
        "tenant_id": "fake_tenant_id",
        "location_name": "fake_location_name",
        "subscription_id": "fake_subscription_id",
        "resource_group": "fake_resource_group",
        "workspace_name": "fake_workspace_name",
        "storage_account": "fake_storage_account",
        "api_connection": "fake_api_connection",
    }


@pytest.fixture
def azure_session(auth_data):
    """Return an AzureSession object."""
    return AzureSession(auth_data)


@pytest.fixture
def azure_provider(auth_data):
    """Return an AzureQuantumProvider object."""
    return AzureQuantumProvider(auth_data)


@pytest.fixture
def build_profile(data: dict[str, Any]) -> TargetProfile:
    """Build a profile for an Azure device."""

    device = data.get("id")

    if "qpu" not in device:
        device_type = DeviceType.SIMULATOR
    else:
        device_type = DeviceType.QPU

    if "rigetti" in device:
        program_spec = ProgramSpec(pyquil.Program)
    else:
        program_spec = ProgramSpec(openqasm3.ast.Program)

    queue_time = data.get("averageQueueTime")
    status = data.get("status")

    return TargetProfile(
        device_id=data.get("id"),
        device_type=device_type,
        program_spec=program_spec,
        queue_time=queue_time,
        status=status,
    )


@pytest.fixture
def azure_device(azure_provider, azure_session):
    """Return an AzureQuantumDevice object."""
    target_profile = azure_provider._build_profile(
        {
            "id": "quantinuum.sim.h1-1e",
            "status": "Available",
            "isAvailable": True,
            "nextAvailable": None,
            "availablilityCD": "",
            "averageQueueTime": 0,
        }
    )
    return AzureQuantumDevice(profile=target_profile, session=azure_session)


@pytest.fixture
def create_azure_device_for_status_test(azure_session):
    """Return a function to create an AzureQuantumDevice object for status tests."""

    def _create_device(status):
        """Create an AzureQuantumDevice object with the given status."""
        data = {
            "id": "quantinuum.sim.h1-1e",
            "status": status,
            "isAvailable": True,
            "nextAvailable": None,
            "availablilityCD": "",
            "averageQueueTime": 0,
        }

        device = data.get("id")
        device_type = DeviceType.SIMULATOR if "qpu" not in device else DeviceType.QPU
        program_spec = (
            ProgramSpec(pyquil.Program)
            if "rigetti" in device
            else ProgramSpec(openqasm3.ast.Program)
        )

        target_profile = TargetProfile(
            device_id=data.get("id"),
            device_type=device_type,
            program_spec=program_spec,
            queue_time=data.get("averageQueueTime"),
            status=data.get("status"),
        )

        return AzureQuantumDevice(profile=target_profile, session=azure_session)

    return _create_device


@pytest.fixture
def azure_job(azure_session):
    """Return an AzureJob object."""
    return AzureJob(job_id="fake_job_id", session=azure_session)


# ---------------SESSION TESTS---------------------
# Test suite for AzureSession.
# --------------------------------------------------


def test_get_access_token(azure_session):
    """Test get_access_token method of AzureSession."""
    with patch.object(
        Session, "post", return_value=Mock(json=lambda: {"access_token": "fake_token"})
    ) as mock_post:
        token = azure_session.get_access_token("quantum")
        assert token == "fake_token"
        mock_post.assert_called_once()


def test_get_auth_headers(azure_session):
    """Test get_auth_headers method of AzureSession."""
    with patch.object(AzureSession, "get_access_token", return_value="fake_token"):
        headers = azure_session.get_auth_headers("quantum")
        assert headers == {
            "Content-type": "application/json",
            "Authorization": "Bearer fake_token",
        }


def test_get_request(azure_session):
    """Test get method of AzureSession."""
    with patch.object(Session, "get", return_value="response") as mock_get:
        with patch.object(
            AzureSession, "get_auth_headers", return_value={"Authorization": "Bearer fake_token"}
        ):
            response = azure_session.get("fake_url")
            assert response == "response"
            mock_get.assert_called_once_with(
                "fake_url", headers={"Authorization": "Bearer fake_token"}
            )


def test_put_request(azure_session):
    """Test put method of AzureSession."""
    with patch.object(Session, "put", return_value="response") as mock_put:
        with patch.object(
            AzureSession, "get_auth_headers", return_value={"Authorization": "Bearer fake_token"}
        ):
            response = azure_session.put("fake_url", {"data": "value"}, "put_type")
            assert response == "response"
            mock_put.assert_called_once_with(
                "fake_url", json={"data": "value"}, headers={"Authorization": "Bearer fake_token"}
            )


def test_post_request(azure_session):
    """Test post method of AzureSession."""
    with patch.object(Session, "post", return_value="response") as mock_post:
        with patch.object(
            AzureSession, "get_auth_headers", return_value={"Authorization": "Bearer fake_token"}
        ):
            payload = {"data": "value"}
            response = azure_session.post(payload)
            assert response == "response"
            expected_url = (
                f"https://{azure_session.location_name}.quantum.azure.com/subscriptions/{azure_session.subscription_id}"
                f"/resourceGroups/{azure_session.resource_group}/providers/Microsoft.Quantum/workspaces/"
                f"{azure_session.workspace_name}/storage/sasUri?api-version=2022-09-12-preview"
            )
            mock_post.assert_called_once_with(
                expected_url, json=payload, headers={"Authorization": "Bearer fake_token"}
            )


def test_delete_request(azure_session):
    """Test delete method of AzureSession."""
    with patch.object(Session, "delete", return_value="response") as mock_delete:
        with patch.object(
            AzureSession, "get_auth_headers", return_value={"Authorization": "Bearer fake_token"}
        ):
            response = azure_session.delete("fake_job")
            assert response == "response"
            expected_url = (
                f"https://{azure_session.location_name}.quantum.azure.com/subscriptions/"
                f"{azure_session.subscription_id}/resourceGroups/{azure_session.resource_group}/"
                f"providers/Microsoft.Quantum/workspaces/{azure_session.workspace_name}/jobs/"
                f"fake_job?api-version=2022-09-12-preview"
            )
            mock_delete.assert_called_once_with(
                expected_url, headers={"Authorization": "Bearer fake_token"}
            )


# ---------------PROVIDER TESTS---------------------
# Test suite for AzureQuantumProvider.
# --------------------------------------------------


def test_build_profile(azure_provider):
    """Test _build_profile method of AzureQuantumProvider."""
    data = {"id": "fake_device_id_qpu_rigetti", "averageQueueTime": 1234, "status": "Available"}
    profile = azure_provider._build_profile(data)

    assert profile._data["device_id"] == data["id"]
    assert profile._data["device_type"] == "QPU"


def test_get_devices(azure_provider, azure_session):
    """Test get_devices method of AzureQuantumProvider."""
    devices_response = {
        "value": [
            {
                "targets": [
                    {
                        "id": "fake_device_id_rigetti_qpu",
                        "currentAvailability": "Available",
                        "averageQueueTime": 1234,
                    },
                    {
                        "id": "fake_device_id_simulator",
                        "currentAvailability": "Available",
                        "averageQueueTime": 5678,
                    },
                ]
            }
        ]
    }

    with patch.object(
        AzureSession, "get", return_value=Mock(json=lambda: devices_response)
    ) as mock_get:
        devices = azure_provider.get_devices()
        assert len(devices[0]) == 2  # quantum_devices
        assert len(devices[1]) == 2  # all_devices

        expected_url = (
            f"https://{azure_session.location_name}.quantum.azure.com/subscriptions/{azure_session.subscription_id}"
            f"/resourceGroups/{azure_session.resource_group}/providers/Microsoft.Quantum/"
            f"workspaces/{azure_session.workspace_name}/providerStatus?api-version=2022-09-12-preview"
        )

        mock_get.assert_called_once_with(expected_url)


def test_get_device(azure_provider):
    """Test get_device method of AzureQuantumProvider."""
    devices_response = {
        "value": [
            {
                "targets": [
                    {
                        "id": "fake_device_id",
                        "currentAvailability": "Available",
                        "averageQueueTime": 1234,
                    }
                ]
            }
        ]
    }

    with patch.object(AzureSession, "get", return_value=Mock(json=lambda: devices_response)):
        device = azure_provider.get_device("fake_device_id")
        assert isinstance(device, AzureQuantumDevice)
        assert device.profile._data["device_id"] == "fake_device_id"


def test_get_device_not_found(azure_provider):
    """Test get_device method of AzureQuantumProvider with non-existent device."""
    devices_response = {
        "value": [
            {
                "targets": [
                    {
                        "id": "fake_device_id",
                        "currentAvailability": "Available",
                        "averageQueueTime": 1234,
                    }
                ]
            }
        ]
    }

    with patch.object(AzureSession, "get", return_value=Mock(json=lambda: devices_response)):
        with pytest.raises(AttributeError):
            azure_provider.get_device("non_existent_device_id")


# ---------------DEVICE TESTS---------------------
# Test suite for AzureQuantumDevice.
# --------------------------------------------------


def test_status_available(create_azure_device_for_status_test):
    """Test status method of AzureQuantumDevice with status 'Available'."""
    device = create_azure_device_for_status_test("Available")
    assert device.status() == DeviceStatus.ONLINE


def test_status_deprecated(create_azure_device_for_status_test):
    """Test status method of AzureQuantumDevice with status 'Deprecated'."""
    device = create_azure_device_for_status_test("Deprecated")
    assert device.status() == DeviceStatus.UNAVAILABLE


def test_status_unavailable(create_azure_device_for_status_test):
    """Test status method of AzureQuantumDevice with status 'Unavailable'."""
    device = create_azure_device_for_status_test("Unavailable")
    assert device.status() == DeviceStatus.OFFLINE


def test_status_unknown(create_azure_device_for_status_test):
    """Test status method of AzureQuantumDevice with status 'Unknown'."""
    device = create_azure_device_for_status_test("Unknown")
    assert device.status() is None


@pytest.mark.parametrize("status", [None, "", 123])
def test_status_invalid(create_azure_device_for_status_test, status):
    """Test status method of AzureQuantumDevice with invalid status."""
    device = create_azure_device_for_status_test(status)
    assert device.status() is None


def test_status(azure_device):
    """Test status method of AzureQuantumDevice."""
    assert azure_device.status() == DeviceStatus.ONLINE


def test_session_property(azure_device, azure_session):
    """Test session property of AzureQuantumDevice."""
    assert azure_device.session == azure_session


def test_create_container(azure_device, azure_session):
    """Test create_container method of AzureQuantumDevice."""
    with patch.object(AzureSession, "put", return_value=Mock()) as mock_put:
        with patch("uuid.uuid4", return_value=uuid4()):
            job_id, container_name = azure_device.create_container()

            expected_url = (
                f"https://management.azure.com/subscriptions/{azure_session.subscription_id}/resourceGroups/"
                f"{azure_session.resource_group}/providers/Microsoft.Storage/storageAccounts/{azure_session.storage_account}"
                f"/blobServices/default/containers/{container_name}?api-version=2022-09-01"
            )

            mock_put.assert_called_once_with(expected_url, payload={}, put_type="storage")
            assert job_id in container_name


# pylint: disable=unused-argument, disable=unused-variable
def test_create_job_routes(azure_device, azure_session):
    """Test create_job_routes method of AzureQuantumDevice."""
    blob_service_client_mock = Mock(spec=BlobServiceClient)
    blob_client_mock = Mock()
    blob_service_client_mock.get_blob_client.return_value = blob_client_mock

    with patch.object(
        BlobServiceClient, "from_connection_string", return_value=blob_service_client_mock
    ):
        with patch.object(
            AzureSession, "post", return_value=Mock(json=lambda: {"sasUri": "fake_sas_uri"})
        ) as mock_post:
            container_sas_uri, input_sas_uri, output_sas_uri = azure_device.create_job_routes(
                "fake_container", "fake_qasm"
            )

            assert container_sas_uri == "fake_sas_uri"
            assert input_sas_uri == "fake_sas_uri"
            assert output_sas_uri == "fake_sas_uri"

            blob_client_mock.upload_blob.assert_any_call(
                "fake_qasm", content_settings=ContentSettings(content_type="application/qasm")
            )
            blob_client_mock.upload_blob.assert_any_call("")


def test_create_payload(azure_device):
    """Test create_payload method of AzureQuantumDevice."""
    payload = azure_device.create_payload(
        container_uri="fake_container_uri",
        input_uri="fake_input_uri",
        output_uri="fake_output_uri",
        job_id="fake_job_id",
        job_name="fake_job_name",
        input_data_format="honeywell.openqasm.v1",
        provider="quantinuum",
        backend="quantinuum.qpu.h1-1",
        num_qubits="fake_num_qubits",
        num_shots=100,
        total_count=100,
        output_data_format="honeywell.quantum-results.v1",
    )

    assert payload["containerUri"] == "fake_container_uri"
    assert payload["id"] == "fake_job_id"
    assert payload["inputDataFormat"] == "honeywell.openqasm.v1"
    assert payload["name"] == "fake_job_name"
    assert payload["providerId"] == "quantinuum"
    assert payload["target"] == "quantinuum.qpu.h1-1"
    assert payload["inputDataUri"] == "fake_input_uri"
    assert payload["inputParams"]["shots"] == 100
    assert payload["outputDataFormat"] == "honeywell.quantum-results.v1"
    assert payload["outputDataUri"] == "fake_output_uri"


def test_submit(azure_device, azure_session):
    """Test submit method of AzureQuantumDevice."""
    with patch.object(
        AzureQuantumDevice, "create_container", return_value=["fake_job_id", "fake_container"]
    ) as mock_create_container:
        with patch.object(
            AzureQuantumDevice,
            "create_job_routes",
            return_value=["fake_container_sas_uri", "fake_input_sas_uri", "fake_output_sas_uri"],
        ) as mock_create_job_routes:
            with patch.object(
                AzureQuantumDevice, "create_payload", return_value={"fake": "payload"}
            ) as mock_create_payload:
                with patch.object(
                    AzureSession, "put", return_value=Mock(json=lambda: {"fake": "response"})
                ) as mock_put:
                    response, submitted_job = azure_device.submit(
                        "fake_input_run", "fake_name", "QPU", 5, 100
                    )

                    assert response == {"fake": "response"}
                    assert isinstance(submitted_job, AzureJob)
                    assert submitted_job._job_id == "fake_job_id"

                    mock_create_container.assert_called_once()
                    mock_create_job_routes.assert_called_once_with(
                        "fake_container", "fake_input_run"
                    )
                    mock_create_payload.assert_called_once()
                    mock_put.assert_called_once()


def test_submit_batch_job(azure_device):
    """Test submit method of AzureQuantumDevice with batch job."""
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Batch jobs (list of inputs) are not supported for this device. Please provide a single job input."
        ),
    ):
        azure_device.submit(["fake_input_run1", "fake_input_run2"], "fake_name", "QPU", 5, 100)


# ------------------JOB TESTS-----------------------
# Test suite for AzureJob.
# --------------------------------------------------


def test_job_session(azure_job, azure_session):
    """Test session property of AzureJob."""
    assert azure_job.session == azure_session


# pylint: disable=function-redefined
def test_get_job_info(azure_job, azure_session):
    """Test get_job_info method of AzureJob."""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "Executing"}

    with patch.object(azure_session, "get", return_value=mock_response) as mock_get:
        job_info = azure_job.get_job_info()

        expected_url = "https://fake_location_name.quantum.azure.com/subscriptions/fake_subscription_id/resourceGroups/fake_resource_group/providers/Microsoft.Quantum/workspaces/fake_workspace_name/jobs/fake_job_id?api-version=2022-09-12-preview"
        mock_get.assert_called_once_with(expected_url)
        assert job_info == {"status": "Executing"}


# pylint: disable=unused-argument
def test_status(azure_job, azure_session):
    """Test status method of AzureJob."""
    statuses = {
        "Waiting": JobStatus.QUEUED,
        "Executing": JobStatus.RUNNING,
        "Failed": JobStatus.FAILED,
        "Cancelled": JobStatus.CANCELLED,
        "Succeeded": JobStatus.COMPLETED,
    }

    for status_str, expected_status in statuses.items():
        with patch.object(azure_job, "get_job_info", return_value={"status": status_str}):
            assert azure_job.status() == expected_status


def test_cancel(azure_job, azure_session):
    """Test cancel method of AzureJob."""
    mock_response = Mock()

    with patch.object(azure_session, "delete", return_value=mock_response) as mock_delete:
        response = azure_job.cancel()
        mock_delete.assert_called_once_with("fake_job_id")
        assert response == mock_response


def test_result(azure_job):
    """Test result method of AzureJob."""
    azure_job.wait_for_final_state = Mock()

    azure_job.get_job_info = Mock(return_value={"status": "Succeeded"})

    mock_blob_service_client = Mock(spec=BlobServiceClient)
    mock_container_client = Mock()
    mock_blob_client = Mock()
    mock_blob_service_client.get_container_client.return_value = mock_container_client
    mock_container_client.get_blob_client.return_value = mock_blob_client

    mock_blob = Mock()
    mock_blob.readall.return_value = b'{"result": "success"}'
    mock_blob_client.download_blob.return_value = mock_blob

    with patch(
        "azure.storage.blob.BlobServiceClient.from_connection_string",
        return_value=mock_blob_service_client,
    ):
        result = azure_job.result()

    assert result == '{"result": "success"}'
    azure_job.wait_for_final_state.assert_called_once()
    azure_job.get_job_info.assert_called_once()
    mock_blob_service_client.get_container_client.assert_called_once_with(
        f"job-{azure_job._job_id}"
    )
    mock_container_client.get_blob_client.assert_called_once_with("rawOutputData")
    mock_blob_client.download_blob.assert_called_once()


def test_result_failure(azure_job):
    """Test result method of AzureJob with failed job."""
    azure_job.wait_for_final_state = Mock()

    azure_job.get_job_info = Mock(
        return_value={
            "status": "Failed",
            "Failed": {"code": "ERROR_CODE", "error": "Job failed message"},
        }
    )

    with pytest.raises(ValueError) as exc_info:
        azure_job.result()

    assert str(exc_info.value) == "Job failed with code ERROR_CODE: Job failed message"
    azure_job.wait_for_final_state.assert_called_once()
    azure_job.get_job_info.assert_called_once()

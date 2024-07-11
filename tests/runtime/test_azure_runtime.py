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
Unit tests for Azure session, provider, and device classes

"""
from unittest.mock import MagicMock, patch
from uuid import UUID

import openqasm3
import pytest
from qiskit import QuantumCircuit, qasm2

from qbraid.runtime.azure.device import AzureQuantumDevice
from qbraid.runtime.azure.provider import AzureHelperFunctions, AzureQuantumProvider, AzureSession
from qbraid.runtime.profile import ProgramSpec, TargetProfile

session = AzureSession(
    client_id="client_id",
    client_secret="client_secret",
    tenant_id="tenant_id",
    location_name="location_name",
    subscription_id="subscription_id",
    resource_group_name="resource_group",
    workspace_name="workspace_name",
    storage_account="storage_account",
    connection_string="connection_string",
)

provider = AzureQuantumProvider(
    client_id="client_id",
    client_secret="client_secret",
    tenant_id="tenant_id",
    location_name="location_name",
    subscription_id="subscription_id",
    resource_group_name="resource_group",
    workspace_name="workspace_name",
    storage_account="storage_account",
    connection_string="connection_string",
)

device = AzureQuantumDevice(
    profile=TargetProfile(
        device_id="microsoft.estimator",
        device_type="SIMULATOR",
        program_spec=ProgramSpec(openqasm3.ast.Program),
        queue_time=0,
        status="Available",
    ),
    session=session,
)
helper_functions = AzureHelperFunctions()


@pytest.fixture
def circuit():
    """Create a sample quantum circuit."""
    test_circuit = QuantumCircuit(2)
    test_circuit.h(0)
    test_circuit.cx(0, 1)
    test_circuit.measure_all()
    qasm_str = qasm2.dumps(test_circuit)

    return qasm_str


@pytest.fixture
def job_data():
    """Create a sample job data for Azure Quantum."""
    test_job_data = {
        "containerUri": "mock.com",
        "inputDataUri": "mock.net",
        "inputDataFormat": "honeywell.openqasm.v1",
        "inputParams": {"shots": 100, "count": 100},
        "metadata": {
            "qiskit": "True",
            "name": "job-data-test-cases",
            "num_qubits": "2",
            "metadata": "null",
            "meas_map": "[0]",
        },
        "sessionId": None,
        "status": "Waiting",
        "jobType": "QuantumComputing",
        "outputDataFormat": "honeywell.quantum-results.v1",
        "outputDataUri": "mock.org",
        "beginExecutionTime": None,
        "cancellationTime": None,
        "quantumComputingData": None,
        "errorData": None,
        "isCancelling": False,
        "tags": [],
        "name": "job-data-test-cases",
        "id": "mock_id",
        "providerId": "quantinuum",
        "target": "quantinuum.sim.h1-1e",
        "creationTime": "2024-06-19T15:10:32.1074886+00:00",
        "endExecutionTime": None,
        "costEstimate": None,
        "itemType": "Job",
    }
    return test_job_data


@pytest.fixture
def device_dict():
    """Create a sample device dictionary for Azure Quantum."""
    test_device_dict = {
        "id": "microsoft.estimator",
        "status": "Available",
        "isAvailable": True,
        "nextAvailable": None,
        "availablilityCD": "",
        "averageQueueTime": 0,
    }
    return test_device_dict


@pytest.fixture
def check_job_data():
    """Check parameters for Azure Quantum job."""
    test_check_parameters = [
        "containerUri",
        "inputDataUri",
        "inputDataFormat",
        "inputParams",
        "metadata",
        "sessionId",
        "status",
        "jobType",
        "outputDataFormat",
        "outputDataUri",
        "beginExecutionTime",
        "cancellationTime",
        "quantumComputingData",
        "errorData",
        "isCancelling",
        "tags",
        "name",
        "id",
        "providerId",
        "target",
        "creationTime",
        "endExecutionTime",
        "costEstimate",
        "itemType",
    ]

    return test_check_parameters


@pytest.fixture
def raw_devices_data():
    """Check devices for Azure Quantum provider."""
    test_raw_devices_data = {
        "value": [
            {
                "id": "ionq",
                "currentAvailability": "Degraded",
                "targets": [
                    {
                        "id": "ionq.qpu",
                        "currentAvailability": "Available",
                        "averageQueueTime": 91639,
                        "statusPage": "https://status.ionq.co",
                    },
                    {
                        "id": "ionq.qpu.aria-1",
                        "currentAvailability": "Unavailable",
                        "averageQueueTime": 1525802,
                        "statusPage": "https://status.ionq.co",
                    },
                    {
                        "id": "ionq.qpu.aria-2",
                        "currentAvailability": "Unavailable",
                        "averageQueueTime": 1097474,
                        "statusPage": "https://status.ionq.co",
                    },
                    {
                        "id": "ionq.simulator",
                        "currentAvailability": "Available",
                        "averageQueueTime": 3,
                        "statusPage": "https://status.ionq.co",
                    },
                ],
            },
            {
                "id": "microsoft-qc",
                "currentAvailability": "Available",
                "targets": [
                    {
                        "id": "microsoft.estimator",
                        "currentAvailability": "Available",
                        "averageQueueTime": 0,
                        "statusPage": None,
                    }
                ],
            },
            {
                "id": "quantinuum",
                "currentAvailability": "Degraded",
                "targets": [
                    {
                        "id": "quantinuum.qpu.h1-1",
                        "currentAvailability": "Degraded",
                        "averageQueueTime": 0,
                        "statusPage": "https://www.quantinuum.com/hardware/h1",
                    },
                    {
                        "id": "quantinuum.sim.h1-1sc",
                        "currentAvailability": "Available",
                        "averageQueueTime": 0,
                        "statusPage": "https://www.quantinuum.com/hardware/h1",
                    },
                    {
                        "id": "quantinuum.sim.h1-1e",
                        "currentAvailability": "Available",
                        "averageQueueTime": 66,
                        "statusPage": "https://www.quantinuum.com/hardware/h1",
                    },
                ],
            },
            {
                "id": "rigetti",
                "currentAvailability": "Degraded",
                "targets": [
                    {
                        "id": "rigetti.sim.qvm",
                        "currentAvailability": "Available",
                        "averageQueueTime": 5,
                        "statusPage": "https://rigetti.statuspage.io/",
                    },
                    {
                        "id": "rigetti.qpu.ankaa-2",
                        "currentAvailability": "Degraded",
                        "averageQueueTime": 5,
                        "statusPage": "https://rigetti.statuspage.io/",
                    },
                ],
            },
        ],
        "nextLink": None,
    }
    return test_raw_devices_data


@pytest.fixture
def raw_device_data():
    """Check device data for Azure Quantum provider."""
    test_raw_device_data = {
        "id": "microsoft.estimator",
        "status": "Available",
        "isAvailable": True,
        "nextAvailable": None,
        "availablilityCD": "",
        "averageQueueTime": 0,
    }
    return test_raw_device_data


@pytest.fixture
def targets():
    """Check targets for Azure Quantum provider."""
    test_targets = [
        "microsoft.estimator",
        "quantinuum.qpu.h1-1",
        "quantinuum.sim.h1-1sc",
        "quantinuum.sim.h1-1e",
        "rigetti.sim.qvm",
        "rigetti.qpu.ankaa-2",
    ]
    return test_targets


@pytest.fixture
def expected_device_parameters():
    """Expected parameters for Azure Quantum device."""
    test_expected_device_parameters = [
        "id",
        "status",
        "isAvailable",
        "nextAvailable",
        "availablilityCD",
        "averageQueueTime",
    ]
    return test_expected_device_parameters


@pytest.fixture
def container():
    """Container for Azure Quantum job."""
    return ["326fh5817-dh27-27fh-dkl83-26fh4j1n37fi", "job-326fh5817-dh27-27fh-dkl83-26fh4j1n37fi"]


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_session_get_devices(
    mock_get, mock_access_token, raw_devices_data, expected_device_parameters
):
    """Test getting data for all Azure Quantum devices."""
    mock_access_token.return_value = "abc123"
    mock_get.return_value = MagicMock()
    mock_get.return_value.json.return_value = raw_devices_data

    devices = session.get_devices()
    all_devices = list(devices[0].keys())

    print(all_devices)

    assert all_devices == expected_device_parameters


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_session_get_device(
    mock_get, mock_access_token, raw_devices_data, expected_device_parameters
):  # pylint: disable=too-many-arguments
    """Getting data for specific Azure Quantum device."""
    mock_access_token.return_value = "abc123"

    mock_get.return_value = MagicMock()
    mock_get.return_value.json.return_value = raw_devices_data

    device = session.get_device("microsoft.estimator")
    device_parameters = list(device.keys())

    assert device_parameters == expected_device_parameters


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions")
def test_session_create_job(mock_helpers):  # pylint: disable=too-many-arguments
    """Test creating a new job through the Azure Quantum API."""
    mock_helpers.quantum_access_token.return_value = "quantum_token"
    mock_helpers.storage_access_token.return_value = "storage_token"
    mock_helpers.create_container.return_value = ("job_id", "container_name")
    mock_helpers.create_job_routes.return_value = (
        "containerSasUri",
        "inputSasUri",
        "outputSasUri",
        "job_headers",
    )
    mock_helpers.create_payload.return_value = "job_payload"
    mock_helpers.submit_job.return_value = {"job": "approved"}

    session._helpers = mock_helpers
    session.formats = {"quantinuum": ("input_format", "output_format")}
    session.backends = {"Emulator": "emulator_backend"}

    input_run = "input_data"
    job = session.create_job(input_run, "job_name", "quantinuum", "Emulator", 2)

    assert job == {"job": "approved"}

    # Verify that all helper methods were called with correct arguments
    mock_helpers.quantum_access_token.assert_called_once_with(
        session.client_id, session.client_secret, session.tenant_id, session.session
    )
    mock_helpers.storage_access_token.assert_called_once_with(
        session.client_id, session.client_secret, session.tenant_id, session.session
    )
    mock_helpers.create_container.assert_called_once_with(
        "storage_token",
        session.subscription_id,
        session.resource_group_name,
        session.storage_account,
        session.session,
    )
    mock_helpers.create_job_routes.assert_called_once_with(
        session.session,
        "container_name",
        input_run,
        session.connection_string,
        session.location_name,
        session.subscription_id,
        session.resource_group_name,
        session.workspace_name,
        "quantum_token",
    )
    mock_helpers.create_payload.assert_called_once_with(
        "containerSasUri",
        "inputSasUri",
        "outputSasUri",
        "job_id",
        job_name="job_name",
        input_data_format="input_format",
        provider="quantinuum",
        backend="emulator_backend",
        num_qubits=2,
        num_shots=100,
        total_count=100,
        output_data_format="output_format",
    )
    mock_helpers.submit_job.assert_called_once_with(
        "job_id",
        "job_payload",
        "job_headers",
        session.location_name,
        session.subscription_id,
        session.resource_group_name,
        session.workspace_name,
        session.session,
    )

    assert session.jobs["job_id"] == ["job_headers", "container_name"]


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions")
@patch("qbraid.runtime.azure.provider.Session.get")  # Patch the get method of the global session
def test_session_get_job(mock_get, mock_helpers):
    """Test getting job data from the Azure Quantum API."""
    mock_helpers.quantum_access_token.return_value = "quantum_token"
    mock_helpers.storage_access_token.return_value = "storage_token"
    mock_helpers.create_container.return_value = ("job_id", "container_name")
    mock_helpers.create_job_routes.return_value = (
        "containerSasUri",
        "inputSasUri",
        "outputSasUri",
        {"Authorization": "Bearer test_token"},
    )
    mock_helpers.create_payload.return_value = "job_payload"
    mock_helpers.submit_job.return_value = {"job": "approved", "id": "job_id"}

    session._helpers = mock_helpers

    session.formats = {"quantinuum": ("input_format", "output_format")}
    session.backends = {"Emulator": "emulator_backend"}

    input_run = "input_data"
    created_job = session.create_job(input_run, "job_name", "quantinuum", "Emulator", 2)

    assert created_job == {"job": "approved", "id": "job_id"}
    assert session.jobs["job_id"] == [{"Authorization": "Bearer test_token"}, "container_name"]

    job_data = {"id": "job_id", "status": "Completed"}
    mock_response = MagicMock()
    mock_response.json.return_value = job_data
    mock_get.return_value = mock_response

    retrieved_job = session.get_job("job_id")

    expected_url = (
        f"https://{session.location_name}.quantum.azure.com/subscriptions/{session.subscription_id}"
        f"/resourceGroups/{session.resource_group_name}/providers/Microsoft.Quantum/workspaces/"
        f"{session.workspace_name}/jobs/job_id?api-version=2022-09-12-preview"
    )
    mock_get.assert_called_once_with(expected_url, headers={"Authorization": "Bearer test_token"})
    assert retrieved_job == job_data

    with pytest.raises(KeyError):
        session.get_job("non_existent_job_id")


def test_get_job_data():
    """Test getting data from a specific Azure Quantum job."""
    job_id = "test_job_id"
    container_name = "test_container"
    session.jobs = {job_id: [{"some": "header"}, container_name]}
    session.connection_string = "test_connection_string"

    mock_helpers = MagicMock()
    mock_data = {"result": "quantum_data"}
    mock_helpers.get_output_data.return_value = mock_data

    session._helpers = mock_helpers

    result = session.get_job_data(job_id)

    session._helpers.get_output_data.assert_called_once_with(
        container_name, session.connection_string
    )
    assert result == mock_data


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions")
@patch("qbraid.runtime.azure.provider.Session.delete")  # Patch the get method of the global session
def test_session_cancel_job(mock_delete, mock_helpers):
    """Test cancelling a job through the Azure Quantum API."""
    mock_helpers.quantum_access_token.return_value = "quantum_token"
    mock_helpers.storage_access_token.return_value = "storage_token"
    mock_helpers.create_container.return_value = ("job_id", "container_name")
    mock_helpers.create_job_routes.return_value = (
        "containerSasUri",
        "inputSasUri",
        "outputSasUri",
        {"Authorization": "Bearer test_token"},
    )
    mock_helpers.create_payload.return_value = "job_payload"
    mock_helpers.submit_job.return_value = {"job": "approved", "id": "job_id"}

    session._helpers = mock_helpers

    session.formats = {"quantinuum": ("input_format", "output_format")}
    session.backends = {"Emulator": "emulator_backend"}

    input_run = "input_data"
    created_job = session.create_job(input_run, "job_name", "quantinuum", "Emulator", 2)

    assert created_job == {"job": "approved", "id": "job_id"}
    assert session.jobs["job_id"] == [{"Authorization": "Bearer test_token"}, "container_name"]

    mock_response = MagicMock()
    mock_response.status_code = 204  # Assuming 204 No Content for successful cancellation
    mock_delete.return_value = mock_response

    cancelled_job = session.cancel_job("job_id")

    expected_url = (
        f"https://{session.location_name}.quantum.azure.com/subscriptions/{session.subscription_id}"
        f"/resourceGroups/{session.resource_group_name}/providers/Microsoft.Quantum/workspaces/"
        f"{session.workspace_name}/jobs/job_id?api-version=2022-09-12-preview"
    )
    mock_delete.assert_called_once_with(
        expected_url, headers={"Authorization": "Bearer test_token"}
    )
    assert cancelled_job == str(mock_response)


@patch("qbraid.runtime.azure.provider.Session.post")
def test_quantum_access_token(mock_post):
    """Test getting an access token for the Azure Quantum API."""
    client_id = "test_client_id"
    client_secret = "test_client_secret"
    tenant_id = "test_tenant_id"

    expected_token = "mock_access_token"
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": expected_token}
    mock_post.return_value = mock_response

    actual_token = helper_functions.quantum_access_token(
        client_id, client_secret, tenant_id, session
    )

    assert actual_token == expected_token
    mock_post.assert_called_once_with(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://quantum.microsoft.com/.default",
        },
        verify=True,
    )


@patch("qbraid.runtime.azure.provider.Session.post")
def test_storage_access_token(mock_post):
    """Test getting an access token for the Azure Storage API."""
    client_id = "test_client_id"
    client_secret = "test_client_secret"
    tenant_id = "test_tenant_id"

    expected_token = "mock_access_token"
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": expected_token}
    mock_post.return_value = mock_response

    actual_token = helper_functions.storage_access_token(
        client_id, client_secret, tenant_id, session
    )

    assert actual_token == expected_token
    mock_post.assert_called_once_with(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://management.azure.com/.default",
        },
        verify=True,
    )


@patch("uuid.uuid4")
@patch("qbraid.runtime.azure.provider.Session.put")  # Patch the get method of the global session
def test_create_container(mock_uuid4, mock_put):
    """Test creating a container for an Azure Quantum job."""
    mock_uuid4.return_value = UUID("ed8d6ef0-c3d8-4f34-8893-d133eb165177")

    token = "dummy_token"
    subscription_id = "dummy_subscription_id"
    resource_group_name = "dummy_resource_group"
    storage_account_name = "dummy_storage_account"

    mock_put.put.return_value = MagicMock()

    result = AzureHelperFunctions.create_container(
        token, subscription_id, resource_group_name, storage_account_name, session
    )

    assert isinstance(result, list)
    assert len(result) == 2
    assert len(result[0]) == 36
    assert len(result[1]) == 40  # Check if container name is correctly formatted


@patch("azure.storage.blob.BlobServiceClient.from_connection_string")
@patch("qbraid.runtime.azure.provider.Session.post")
# pylint: disable=unused-argument
def test_create_job_routes(mock_connection_string, mock_session_post):
    """Test creating routes for an Azure Quantum job."""
    container = "test_container"
    qasm = "test_qasm"
    connection_string = "test_connection_string"
    location_name = "test_location"
    subscription_id = "test_subscription"
    resource_group_name = "test_resource_group"
    workspace_name = "test_workspace"
    quantum_access_token = "test_token"

    mock_session_post.return_value = MagicMock()
    mock_session_post.return_value.json.return_value = {"sasUri": "mock_sas_uri"}

    result = helper_functions.create_job_routes(
        session,
        container,
        qasm,
        connection_string,
        location_name,
        subscription_id,
        resource_group_name,
        workspace_name,
        quantum_access_token,
    )
    assert len(result) == 4


def test_create_payload():
    """Test creating a payload for an Azure Quantum job."""
    # Test data
    container_uri = "https://example.com/container"
    input_uri = "https://example.com/input"
    output_uri = "https://example.com/output"
    job_id = "Test-Job"
    job_name = "job-Test-Job"
    input_data_format = "honeywell.openqasm.v1"
    provider = "dummy_provider"
    backend = "dummy_backend"
    num_qubits = "5"
    num_shots = 100
    total_count = 100
    output_data_format = "honeywell.quantum-results.v1"

    # Call the function under test
    payload = AzureHelperFunctions.create_payload(
        container_uri,
        input_uri,
        output_uri,
        job_id,
        job_name,
        input_data_format,
        provider,
        backend,
        num_qubits,
        num_shots,
        total_count,
        output_data_format,
    )

    # Assertions
    assert isinstance(payload, dict)
    assert payload["containerUri"] == container_uri
    assert payload["id"] == "Test-Job"
    assert payload["inputDataFormat"] == input_data_format
    assert payload["itemType"] == "Job"
    assert payload["name"] == job_name
    assert payload["providerId"] == provider
    assert payload["target"] == backend
    assert payload["inputDataUri"] == input_uri
    assert payload["inputParams"]["shots"] == num_shots
    assert payload["inputParams"]["count"] == total_count
    assert payload["outputDataFormat"] == output_data_format
    assert payload["outputDataUri"] == output_uri
    assert payload["metadata"]["qiskit"] == "True"
    assert payload["metadata"]["name"] == job_name
    assert payload["metadata"]["num_qubits"] == num_qubits
    assert payload["metadata"]["metadata"] == "null"
    assert payload["metadata"]["meas_map"] == "[0]"


@patch(
    "qbraid.runtime.azure.provider.Session.put"
)  # Adjust the import based on your project structure
def test_submit_job(mock_put):
    """Test submitting a job to the Azure Quantum API."""
    job_id = "job_id"
    payload = {"key": "value"}
    job_header = {"Authorization": "Bearer test_token"}
    location_name = "location_name"
    subscription_id = "subscription_id"
    resource_group_name = "resource_group_name"
    workspace_name = "workspace_name"

    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_put.return_value = mock_response

    result = AzureHelperFunctions.submit_job(
        job_id,
        payload,
        job_header,
        location_name,
        subscription_id,
        resource_group_name,
        workspace_name,
        session,
    )

    expected_url = (
        f"https://{location_name}.quantum.azure.com/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group_name}/providers/Microsoft.Quantum/workspaces/"
        f"{workspace_name}/jobs/{job_id}?api-version=2022-09-12-preview"
    )
    mock_put.assert_called_once_with(expected_url, json=payload, headers=job_header)
    assert result == {"status": "success"}


@patch("qbraid.runtime.azure.provider.BlobServiceClient")
def test_get_output_data(mock_blob_service_client_class):
    """Test getting output data from an Azure Quantum job."""
    # Mock the BlobServiceClient instance
    mock_blob_service_client = MagicMock()
    mock_blob_service_client_class.from_connection_string.return_value = mock_blob_service_client

    # Mock the container client
    mock_container_client = MagicMock()
    mock_blob_service_client.get_container_client.return_value = mock_container_client

    # Mock the blob client
    mock_blob_client = MagicMock()
    mock_container_client.get_blob_client.return_value = mock_blob_client

    # Mock the download_blob method and its return value
    mock_blob_data = MagicMock()
    mock_blob_data.readall.return_value = b'{"result": "quantum data"}'
    mock_blob_client.download_blob.return_value = mock_blob_data

    # Test data
    container_name = "test_container"
    connection_string = "test_connection_string"

    # Call the method
    result = AzureHelperFunctions.get_output_data(container_name, connection_string)

    # Assertions
    assert result == '{"result": "quantum data"}'

    # Verify that all methods were called with correct arguments
    mock_blob_service_client_class.from_connection_string.assert_called_once_with(connection_string)
    mock_blob_service_client.get_container_client.assert_called_once_with(container_name)
    mock_container_client.get_blob_client.assert_called_once_with("rawOutputData")
    mock_blob_client.download_blob.assert_called_once()
    mock_blob_data.readall.assert_called_once()


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_provider_get_devices(mock_get, mock_access_token, raw_devices_data):
    """Test getting data for all Azure Quantum devices."""
    mock_access_token.return_value = "abc123"
    mock_get.return_value = MagicMock()
    mock_get.return_value.json.return_value = raw_devices_data

    devices = provider.get_devices()

    assert isinstance(devices[0], AzureQuantumDevice)


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_provider_get_device(
    mock_get, mock_access_token, raw_devices_data
):  # pylint: disable=too-many-arguments
    """Getting data for specific Azure Quantum device."""
    mock_access_token.return_value = "abc123"

    mock_get.return_value = MagicMock()
    mock_get.return_value.json.return_value = raw_devices_data

    device = provider.get_device("microsoft.estimator")

    assert isinstance(device, AzureQuantumDevice)


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_device_status(mock_get, mock_access_token, raw_devices_data):
    """Test getting status of AzureQuantumDevice."""
    mock_access_token.return_value = "abc123"

    mock_get.return_value = MagicMock()
    mock_get.return_value.json.return_value = raw_devices_data

    device = provider.get_device("microsoft.estimator")

    assert "status" in device.profile


def test_device_session():
    """Test the session property of the AzureProvider class."""
    assert device.session == session


def test_device_class_status():
    """Test the status method of the AzureQuantumDevice class."""
    assert device.status() == "Available"


@patch("qbraid.runtime.azure.provider.AzureSession.create_job")
def test_device_job(mock_job):
    """Test the submit method of the AzureQuantumDevice class."""
    mock_job.return_value = "job"
    assert device.submit("run_input", "name", "provider", "backend", "qubits") == "job"

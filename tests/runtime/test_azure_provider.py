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

import pytest
from qiskit import QuantumCircuit, qasm2

from qbraid.runtime.azure.device import AzureQuantumDevice
from qbraid.runtime.azure.provider import AzureQuantumProvider, AzureSession

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
    # Mock data for create_job
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

    # Attach the mocked helpers to the session
    session._helpers = mock_helpers

    # Mock the formats and backends attributes
    session.formats = {"quantinuum": ("input_format", "output_format")}
    session.backends = {"Emulator": "emulator_backend"}

    # Call create_job
    input_run = "input_data"
    created_job = session.create_job(input_run, "job_name", "quantinuum", "Emulator", 2)

    # Verify create_job
    assert created_job == {"job": "approved", "id": "job_id"}
    assert session.jobs["job_id"] == [{"Authorization": "Bearer test_token"}, "container_name"]

    # Mock data for get_job
    job_data = {"id": "job_id", "status": "Completed"}
    mock_response = MagicMock()
    mock_response.json.return_value = job_data
    mock_get.return_value = mock_response

    # Call get_job
    retrieved_job = session.get_job("job_id")

    # Verify get_job
    expected_url = (
        f"https://{session.location_name}.quantum.azure.com/subscriptions/{session.subscription_id}"
        f"/resourceGroups/{session.resource_group_name}/providers/Microsoft.Quantum/workspaces/"
        f"{session.workspace_name}/jobs/job_id?api-version=2022-09-12-preview"
    )
    mock_get.assert_called_once_with(expected_url, headers={"Authorization": "Bearer test_token"})
    assert retrieved_job == job_data

    # Test for job not found
    with pytest.raises(KeyError):
        session.get_job("non_existent_job_id")


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions")
@patch("qbraid.runtime.azure.provider.Session.delete")  # Patch the get method of the global session
def test_session_cancel_job(mock_delete, mock_helpers):
    """Test cancelling a job through the Azure Quantum API."""
    # Mock data for create_job
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

    # Attach the mocked helpers to the session
    session._helpers = mock_helpers

    # Mock the formats and backends attributes
    session.formats = {"quantinuum": ("input_format", "output_format")}
    session.backends = {"Emulator": "emulator_backend"}

    # Call create_job
    input_run = "input_data"
    created_job = session.create_job(input_run, "job_name", "quantinuum", "Emulator", 2)

    # Verify create_job
    assert created_job == {"job": "approved", "id": "job_id"}
    assert session.jobs["job_id"] == [{"Authorization": "Bearer test_token"}, "container_name"]

    # Mock data for get_job
    mock_response = MagicMock()
    mock_response.status_code = 204  # Assuming 204 No Content for successful cancellation
    mock_delete.return_value = mock_response

    # Call cancel_job
    cancelled_job = session.cancel_job("job_id")

    # Verify cancel_job
    expected_url = (
        f"https://{session.location_name}.quantum.azure.com/subscriptions/{session.subscription_id}"
        f"/resourceGroups/{session.resource_group_name}/providers/Microsoft.Quantum/workspaces/"
        f"{session.workspace_name}/jobs/job_id?api-version=2022-09-12-preview"
    )
    mock_delete.assert_called_once_with(
        expected_url, headers={"Authorization": "Bearer test_token"}
    )
    assert cancelled_job == str(mock_response)


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_provider_get_devices(mock_get, mock_access_token, raw_devices_data):
    """Test getting data for all Azure Quantum devices."""
    mock_access_token.return_value = "abc123"
    mock_get.return_value = MagicMock()
    mock_get.return_value.json.return_value = raw_devices_data

    devices = provider.get_devices()

    assert isinstance(devices[0], AzureQuantumDevice)


# @pytest.mark.skip('almost bruh')
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


# @pytest.mark.skip('almost bruh')
@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_device_status(mock_get, mock_access_token, raw_devices_data):
    """Test getting status of AzureQuantumDevice."""
    mock_access_token.return_value = "abc123"

    mock_get.return_value = MagicMock()
    mock_get.return_value.json.return_value = raw_devices_data

    device = provider.get_device("microsoft.estimator")

    assert "status" in device.profile

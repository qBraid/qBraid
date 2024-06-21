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
from unittest.mock import patch

import pytest
from qiskit import QuantumCircuit, qasm2

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


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_session_get_devices(mock_access_token, mock_device_data, raw_devices_data, targets):
    """Test getting data for all Azure Quantum devices."""
    mock_access_token.return_value = "abc123"
    mock_device_data.return_value = raw_devices_data

    devices = session.get_devices()
    all_devices = list(devices[0].keys())
    assert all_devices == targets


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_session_get_device(
    mock_access_token, mock_device_data, raw_device_data, expected_device_parameters
):  # pylint: disable=too-many-arguments
    """Getting data for specific Azure Quantum device."""
    mock_access_token.return_value = "abc123"
    mock_device_data.return_value = raw_device_data

    device = session.get_device("microsoft.estimator")
    device_parameters = list(device.keys())

    assert device_parameters == expected_device_parameters


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.storage_access_token")
@patch("qbraid.runtime.azure.provider.Session.post")
def test_session_create_job(
    mock_quantum_token, mock_storage_token, mock_job_data, job_data, circuit, check_job_data
):  # pylint: disable=too-many-arguments
    """Test creating a new job through the Azure Quantum API."""
    mock_quantum_token.return_value = "abc123"
    mock_storage_token.return_value = "def456"
    mock_job_data.return_value = job_data

    job = session.create_job(circuit, "job-data-test-cases", "quantinuum", "Emulator", 2)
    job_parameters = list(job.keys())

    assert job_parameters == check_job_data


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.storage_access_token")
@patch("qbraid.runtime.azure.provider.Session.post")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_session_get_job(
    mock_quantum_token,
    mock_storage_token,
    mock_job_data,
    mock_get_job,
    job_data,
    circuit,
    check_job_data,
):  # pylint: disable=too-many-arguments
    """Test getting a specific Azure Quantum job."""
    mock_quantum_token.return_value = "abc123"
    mock_storage_token.return_value = "def456"
    mock_job_data.return_value = job_data
    mock_get_job.retirm_value = job_data

    session.create_job(circuit, "job-data-test-cases", "quantinuum", "Emulator", 2)

    job_id = next(iter(session.jobs))
    get_job = session.get_job(job_id)
    job_parameters = list(get_job.keys())

    assert job_parameters == check_job_data


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.storage_access_token")
@patch("qbraid.runtime.azure.provider.Session.post")
@patch("qbraid.runtime.azure.provider.Session.get")
@patch("qbraid.runtime.azure.provider.Session.delete")
def test_session_cancel_job(
    mock_quantum_token,
    mock_storage_token,
    mock_job_data,
    mock_get_job,
    mock_delete_job,
    job_data,
    circuit,
):  # pylint: disable=too-many-arguments
    """Test cancelling a specific Azure Quantum job."""
    mock_quantum_token.return_value = "abc123"
    mock_storage_token.return_value = "def456"
    mock_job_data.return_value = job_data
    mock_get_job.return_value = job_data
    mock_delete_job.return_value = "Job has been cancelled"

    session.create_job(circuit, "job-data-test-cases", "quantinuum", "Emulator", 2)
    job_id = next(iter(session.jobs))

    cancelled = session.cancel_job(job_id)

    assert cancelled == "Job has been cancelled"


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_provider_get_devices(mock_access_token, mock_device_data, raw_devices_data, targets):
    """Test getting list of all AzureQuantumDevice objects."""
    mock_access_token.return_value = "abc123"
    mock_device_data.return_value = raw_devices_data

    devices = provider.get_devices()

    all_devices = list(devices[0].keys())
    assert all_devices == targets


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_provider_get_device(mock_access_token, mock_device_data, raw_device_data):
    """Test getting a specific AzureQuantumDevice object."""
    mock_access_token.return_value = "abc123"
    mock_device_data.return_value = raw_device_data

    check_device = "<qbraid.runtime.azure.device.AzureQuantumDevice('microsoft.estimator')>"
    device = str(provider.get_device("microsoft.estimator"))

    assert check_device == device


@patch("qbraid.runtime.azure.provider.AzureHelperFunctions.quantum_access_token")
@patch("qbraid.runtime.azure.provider.Session.get")
def test_device_status(mock_access_token, mock_device_data, device_dict):
    """Test getting status of AzureQuantumDevice."""
    mock_access_token.return_value = "abc123"
    mock_device_data.return_value = device_dict

    devices = provider.session.get_device("microsoft.estimator")
    check = None

    if "status" in devices:
        check = "exists"

    assert check == "exists"

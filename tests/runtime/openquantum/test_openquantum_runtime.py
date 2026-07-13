# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for OpenQuantumProvider class
"""
from unittest.mock import MagicMock, patch

import pytest

from qbraid.runtime import (
    GateModelResultData,
    ResourceNotFoundError,
    Result,
)
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.openquantum import (
    OpenQuantumDevice,
    OpenQuantumJob,
    OpenQuantumProvider,
    OpenQuantumSession,
)

# Mock Data
DEVICE_DATA = {
    "backend_classes": [
        {
            "id": "c1b9a7a3-4b8f-4b3e-8b3e-4b8f4b3e8b3e",
            "name": "OpenQuantum Simulator",
            "description": "A simulator.",
            "type": "SIMULATOR",
            "provider_id": "p1",
            "short_code": "oq-sim",
            "constraint_data": {"max_qubits": 32, "min_qubits": 1},
        },
        {
            "id": "d2c... ",
            "name": "OpenQuantum QPU",
            "description": "A QPU.",
            "type": "QPU",
            "provider_id": "p1",
            "short_code": "oq-qpu-1",
            "constraint_data": {"max_qubits": 25, "min_qubits": 1},
        },
    ],
    "pagination": {"next_cursor": None},
}

ORG_DATA = {"organizations": [{"id": "org_abc123", "name": "Test Org"}]}

UPLOAD_RESPONSE = {"id": "upload_id_123", "url": "https://presigned.url/for/upload"}

PREPARE_RESPONSE = {"id": "prep_id_456"}

PREPARATION_RESULT_COMPLETED = {
    "status": "Completed",
    "quote": [
        {
            "price": 10,
            "execution_plan_id": "072f7eb6-574b-4bae-aafa-d3399c4abe7a",
            "name": "Standard Plan",
            "queue_priorities": [
                {
                    "price_increase": 0,
                    "queue_priority_id": "0f7b91a3-d1bf-46fb-af9c-55b77fa72bed",
                    "name": "Standard Queue",
                },
                {
                    "price_increase": 5,
                    "queue_priority_id": "4ea2b9de-2d20-46d4-b1b5-0b71537a584f",
                    "name": "Fast Queue",
                },
            ],
        }
    ],
}

CREATE_JOB_RESPONSE = {"id": "job_xyz789", "status": "CREATED"}

GET_JOB_RESPONSE_COMPLETED = {
    "id": "job_xyz789",
    "status": "Completed",
    "backend_class_id": "oq-sim",
    "execution_plan_id": "072f7eb6-574b-4bae-aafa-d3399c4abe7a",
    "queue_priority_id": "0f7b91a3-d1bf-46fb-af9c-55b77fa72bed",
    "output_data_url": "https://presigned.url/for/output",
    "message": "Job completed successfully",
}

GET_JOB_RESPONSE_FAILED = {
    "id": "job_xyz789",
    "status": "Failed",
    "backend_class_id": "oq-sim",
    "output_data_url": None,
    "message": "Job failed due to an error",
}

JOB_OUTPUT_RESPONSE = {"00": 50, "11": 50}


@pytest.fixture
def mock_session():
    """Fixture for a mocked OpenQuantumSession."""
    with patch("qbraid.runtime.openquantum.provider.OpenQuantumSession") as MockSession:
        session = MockSession.return_value
        session.get_devices.return_value = DEVICE_DATA["backend_classes"]

        # Mock get_backend_class_details to return constraint data
        def mock_get_details(backend_id):
            if backend_id == "c1b9a7a3-4b8f-4b3e-8b3e-4b8f4b3e8b3e":
                return {"constraint_data": {"max_qubits": 32, "min_qubits": 1}}
            if backend_id == "d2c... ":
                return {"constraint_data": {"max_qubits": 25, "min_qubits": 1}}
            return {}

        session.get_backend_class_details.side_effect = mock_get_details
        session.get_user_organizations.return_value = ORG_DATA["organizations"]
        session.upload_input.return_value = UPLOAD_RESPONSE["id"]
        session.prepare_job.return_value = PREPARE_RESPONSE
        session.wait_for_preparation.return_value = PREPARATION_RESULT_COMPLETED["quote"]
        session.create_job.return_value = CREATE_JOB_RESPONSE
        session.get_job.return_value = GET_JOB_RESPONSE_COMPLETED
        session.download_job_output.return_value = JOB_OUTPUT_RESPONSE
        yield session


@pytest.fixture
def provider(mock_session):
    """Fixture for an OpenQuantumProvider with a mocked session."""
    with patch.object(
        OpenQuantumProvider,
        "__init__",
        lambda s, client_id=None, client_secret=None: setattr(s, "session", mock_session),
    ):
        p = OpenQuantumProvider()
        yield p


def test_openquantum_provider_get_devices(provider):
    """Test getting OpenQuantum provider and devices."""
    assert isinstance(provider, OpenQuantumProvider)

    devices = provider.get_devices()
    assert len(devices) == 2
    assert isinstance(devices[0], OpenQuantumDevice)
    assert devices[0].id == "oq-sim"
    assert devices[0].simulator is True
    assert devices[0].profile.num_qubits == 32
    assert devices[0].profile.constraint_data == {"max_qubits": 32, "min_qubits": 1}
    assert devices[1].id == "oq-qpu-1"
    assert devices[1].simulator is False
    assert devices[1].profile.num_qubits == 25
    assert devices[1].profile.constraint_data == {"max_qubits": 25, "min_qubits": 1}

    aliases = [spec.alias for spec in devices[0].profile.program_spec]
    assert "qasm2" in aliases and "qasm3" in aliases


def test_openquantum_provider_get_device(provider):
    """Test getting a specific device."""
    device = provider.get_device("oq-sim")
    assert isinstance(device, OpenQuantumDevice)
    assert device.id == "oq-sim"
    assert device.simulator is True


def test_provider_device_not_found_error(provider):
    """Test that a ResourceNotFoundError is raised if the device is not found."""
    with pytest.raises(ResourceNotFoundError, match="Device 'fake_device' not found."):
        provider.get_device("fake_device")


def test_openquantum_device_status(provider):
    """Test device status."""
    device = provider.get_device("oq-sim")
    assert device.status() == DeviceStatus.ONLINE


@patch("requests.put")
def test_device_run_and_submit(mock_requests_put, provider):
    """Test running a fake job through the full run/submit flow."""
    mock_requests_put.return_value.raise_for_status.return_value = None
    qasm_input = "OPENQASM 3.0; qubit[2] q; h q[0]; cx q[0], q[1];"

    device = provider.get_device("oq-sim")
    job = device.run(qasm_input, shots=100)

    assert isinstance(job, OpenQuantumJob)
    assert job.id == "job_xyz789"

    provider.session.upload_input.assert_called_once_with(qasm_input.encode("utf-8"))
    provider.session.prepare_job.assert_called_once()
    provider.session.wait_for_preparation.assert_called_once_with("prep_id_456")
    provider.session.create_job.assert_called_once()

    job_status = job.status()
    assert job_status == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, Result)
    assert result.success is True
    assert result.job_id == "job_xyz789"
    assert result.device_id == "oq-sim"
    assert result.details["execution_plan"] == "PUBLIC"
    assert result.details["queue_priority"] == "STANDARD"
    assert isinstance(result.data, GateModelResultData)
    assert result.data.get_counts() == {"00": 50, "11": 50}


@patch("requests.put")
def test_device_submit_dry_run(mock_requests_put, provider):
    """Test submit with dry_run=True."""
    mock_requests_put.return_value.raise_for_status.return_value = None
    qasm_input = "OPENQASM 3.0; qubit[2] q; h q[0];"
    device = provider.get_device("oq-sim")

    quote = device.submit(qasm_input, dry_run=True)

    assert quote == PREPARATION_RESULT_COMPLETED["quote"]
    provider.session.create_job.assert_not_called()


@patch("requests.put")
def test_device_submit_batch(mock_requests_put, provider):
    """Test submitting a batch of jobs."""
    mock_requests_put.return_value.raise_for_status.return_value = None
    qasm_inputs = ["OPENQASM 3.0; h q[0];", "OPENQASM 3.0; x q[0];"]
    device = provider.get_device("oq-sim")

    jobs = device.submit(qasm_inputs)

    assert isinstance(jobs, list)
    assert len(jobs) == 2
    assert all(isinstance(j, OpenQuantumJob) for j in jobs)
    assert provider.session.create_job.call_count == 2


def test_job_result_standalone(provider):
    """Test getting a result from a standalone job with no device attached."""
    provider.session.get_job.return_value = GET_JOB_RESPONSE_COMPLETED
    provider.session.download_job_output.return_value = JOB_OUTPUT_RESPONSE
    job = OpenQuantumJob("job_xyz789", session=provider.session)

    result = job.result()
    assert result.success is True
    assert result.device_id == "oq-sim"


def test_job_failed(provider):
    """Test a failed job result."""
    provider.session.get_job.return_value = GET_JOB_RESPONSE_FAILED
    job = OpenQuantumJob("job_xyz789", session=provider.session)

    assert job.status() == JobStatus.FAILED
    with pytest.raises(QbraidRuntimeError, match="Job failed: Job failed due to an error"):
        job.result()


def test_job_status_mapping(provider):
    """Test the mapping of OpenQuantum statuses to qBraid JobStatus."""
    job = OpenQuantumJob("job_id", session=provider.session)
    statuses = {
        "Created": JobStatus.INITIALIZING,
        "Pending": JobStatus.INITIALIZING,
        "Queued": JobStatus.QUEUED,
        "Running": JobStatus.RUNNING,
        "Completed": JobStatus.COMPLETED,
        "Failed": JobStatus.FAILED,
        "Canceled": JobStatus.CANCELLED,
        "UNKNOWN_STATUS": JobStatus.UNKNOWN,
    }
    for oq_status, qb_status in statuses.items():
        provider.session.get_job.return_value = {"status": oq_status}
        assert job.status() == qb_status


def test_job_cancel(provider):
    """Test cancelling a job."""
    job = OpenQuantumJob("job_id_to_cancel", session=provider.session)
    job.cancel()
    provider.session.cancel_job.assert_called_once_with("job_id_to_cancel")


def test_session_auth_errors(monkeypatch):
    """Test session authentication errors."""
    monkeypatch.setenv("OPENQUANTUM_CLIENT_ID", "")
    monkeypatch.setenv("OPENQUANTUM_CLIENT_SECRET", "")
    with pytest.raises(ValueError, match="OpenQuantum client_id and client_secret are required."):
        OpenQuantumSession()


def test_session_auth_from_env(monkeypatch):
    """Test session authentication from environment variables."""
    monkeypatch.setenv("OPENQUANTUM_CLIENT_ID", "test_id")
    monkeypatch.setenv("OPENQUANTUM_CLIENT_SECRET", "test_secret")
    with patch.object(OpenQuantumSession, "_fetch_token"):
        session = OpenQuantumSession()
        assert session.client_id == "test_id"
        assert session.client_secret == "test_secret"


@patch("requests.put")
def test_device_submit_with_overrides(mock_requests_put, provider):
    """Test submit with explicit organization, plan, and priority IDs."""
    mock_requests_put.return_value.raise_for_status.return_value = None
    qasm_input = "OPENQASM 3.0; h q[0];"
    device = provider.get_device("oq-sim")

    # Explicit overrides using actual UUIDs from mock data
    org_id = "org_override"
    plan_id = "072f7eb6-574b-4bae-aafa-d3399c4abe7a"  # PUBLIC
    prio_id = "4ea2b9de-2d20-46d4-b1b5-0b71537a584f"  # PRIORITY

    job = device.submit(
        qasm_input, organization_id=org_id, execution_plan_id=plan_id, queue_priority_id=prio_id
    )

    # Verify get_user_organizations was NOT called (override used)
    provider.session.get_user_organizations.assert_not_called()

    # Verify create_job called with overrides
    expected_payload = {
        "organization_id": org_id,
        "job_preparation_id": "prep_id_456",
        "execution_plan_id": plan_id,
        "queue_priority_id": prio_id,
    }
    provider.session.create_job.assert_called_with(expected_payload)
    assert isinstance(job, OpenQuantumJob)


@patch("requests.put")
def test_device_submit_with_readable_names(mock_requests_put, provider):
    """Test submit with readable execution_plan and queue_priority names."""
    mock_requests_put.return_value.raise_for_status.return_value = None
    qasm_input = "OPENQASM 3.0; h q[0];"
    device = provider.get_device("oq-sim")

    job = device.submit(qasm_input, execution_plan="public", queue_priority="standard")

    # Verify create_job called with correct UUIDs
    expected_payload = {
        "organization_id": "org_abc123",
        "job_preparation_id": "prep_id_456",
        "execution_plan_id": "072f7eb6-574b-4bae-aafa-d3399c4abe7a",
        "queue_priority_id": "0f7b91a3-d1bf-46fb-af9c-55b77fa72bed",
    }
    provider.session.create_job.assert_called_with(expected_payload)
    assert isinstance(job, OpenQuantumJob)


@patch("requests.put")
def test_device_submit_invalid_readable_names(mock_requests_put, provider):
    """Test validation errors for invalid readable names."""
    mock_requests_put.return_value.raise_for_status.return_value = None
    qasm_input = "OPENQASM 3.0; h q[0];"
    device = provider.get_device("oq-sim")

    with pytest.raises(ValueError, match="Unknown execution plan: invalid_plan"):
        device.submit(qasm_input, execution_plan="invalid_plan")

    with pytest.raises(ValueError, match="Unknown queue priority: invalid_prio"):
        device.submit(qasm_input, queue_priority="invalid_prio")


@patch("requests.put")
def test_device_submit_invalid_overrides(mock_requests_put, provider):
    """Test validation errors for invalid plan/priority overrides."""
    mock_requests_put.return_value.raise_for_status.return_value = None
    qasm_input = "OPENQASM 3.0; h q[0];"
    device = provider.get_device("oq-sim")

    with pytest.raises(ValueError, match="Execution plan 'bad_plan' not found"):
        device.submit(qasm_input, execution_plan_id="bad_plan")

    # Use valid plan ID but invalid priority ID
    valid_plan_id = "072f7eb6-574b-4bae-aafa-d3399c4abe7a"
    with pytest.raises(ValueError, match="Queue priority 'bad_prio' not found"):
        device.submit(qasm_input, execution_plan_id=valid_plan_id, queue_priority_id="bad_prio")


@patch("requests.put")
def test_device_submit_min_total_cost(mock_requests_put, provider):
    """Test submitting with no execution plan or priority selects min total cost."""
    mock_requests_put.return_value.raise_for_status.return_value = None
    qasm_input = "OPENQASM 3.0; h q[0];"
    device = provider.get_device("oq-sim")

    # plan_1 price is cheaper, but total cost is higher (20 vs 17)
    custom_quote = [
        {
            "price": 10,
            "execution_plan_id": "plan_1",
            "queue_priorities": [{"price_increase": 10, "queue_priority_id": "prio_A"}],
        },
        {
            "price": 15,
            "execution_plan_id": "plan_2",
            "queue_priorities": [{"price_increase": 2, "queue_priority_id": "prio_B"}],
        },
    ]
    provider.session.wait_for_preparation.return_value = custom_quote

    device.submit(qasm_input)
    expected_payload = {
        "organization_id": "org_abc123",
        "job_preparation_id": "prep_id_456",
        "execution_plan_id": "plan_2",
        "queue_priority_id": "prio_B",
    }
    provider.session.create_job.assert_called_with(expected_payload)


@patch("requests.put")
def test_device_submit_queue_priority_without_plan(mock_requests_put, provider):
    """Test submitting with a queue priority but no execution plan."""
    mock_requests_put.return_value.raise_for_status.return_value = None
    qasm_input = "OPENQASM 3.0; h q[0];"
    device = provider.get_device("oq-sim")

    # Mock a quote with multiple plans to verify it selects the cheapest valid one
    custom_quote = [
        {
            "price": 10,
            "execution_plan_id": "plan_1",
            "queue_priorities": [{"price_increase": 0, "queue_priority_id": "prio_A"}],
        },
        {
            "price": 20,
            "execution_plan_id": "plan_2",
            "queue_priorities": [
                {"price_increase": 0, "queue_priority_id": "prio_A"},
                {"price_increase": 5, "queue_priority_id": "prio_B"},
            ],
        },
        {
            "price": 5,
            "execution_plan_id": "plan_3",
            "queue_priorities": [{"price_increase": 0, "queue_priority_id": "prio_C"}],
        },
    ]
    provider.session.wait_for_preparation.return_value = custom_quote

    # Requesting prio_B should select plan_2, even though plan_3 is cheapest overall
    device.submit(qasm_input, queue_priority_id="prio_B")
    expected_payload = {
        "organization_id": "org_abc123",
        "job_preparation_id": "prep_id_456",
        "execution_plan_id": "plan_2",
        "queue_priority_id": "prio_B",
    }
    provider.session.create_job.assert_called_with(expected_payload)

    # Requesting a non-existent priority should raise ValueError
    with pytest.raises(
        ValueError, match="Queue priority 'prio_X' not found in any execution plan."
    ):
        device.submit(qasm_input, queue_priority_id="prio_X")


def test_provider_hash(provider):
    """Test OpenQuantumProvider hash."""
    h1 = hash(provider)
    h2 = hash(provider)
    assert h1 == h2


def test_get_devices_details_error(mock_session):
    """Test get_devices when get_backend_class_details fails."""
    mock_session.get_backend_class_details.side_effect = Exception("API down")

    with patch.object(
        OpenQuantumProvider,
        "__init__",
        lambda s, client_id=None, client_secret=None: setattr(s, "session", mock_session),
    ):
        p = OpenQuantumProvider()
        devices = p.get_devices()
        assert len(devices) == 2
        assert devices[0].id == "oq-sim"


@patch("requests.post")
def test_session_fetch_token(mock_post):
    """Test OpenQuantumSession token fetching."""
    mock_post.return_value.json.return_value = {"access_token": "test_token", "expires_in": 300}
    mock_post.return_value.raise_for_status.return_value = None
    session = OpenQuantumSession(client_id="id", client_secret="secret")
    session._fetch_token()
    assert session._token == "test_token"
    assert session._token_expires_at > 0


def test_session_token_provider():
    """A token_provider supplies the bearer token without client_id/secret and
    is re-invoked only when the cached token is near expiry."""
    calls = []

    def provider():
        calls.append(1)
        return (f"user_token_{len(calls)}", 9_999_999_999.0)  # far-future expiry

    # No client_id/secret required when a token_provider is supplied.
    session = OpenQuantumSession(token_provider=provider)
    session._ensure_token()
    assert session._token == "user_token_1"
    assert len(calls) == 1

    # Still fresh -> provider not called again.
    session._ensure_token()
    assert len(calls) == 1

    # Expired -> provider re-invoked for a new token (covers long prepare waits).
    session._token_expires_at = 0
    session._ensure_token()
    assert session._token == "user_token_2"
    assert len(calls) == 2


@patch("requests.post")
@patch("qbraid_core.sessions.Session.request")
def test_session_request(mock_super_request, mock_post):
    """Test OpenQuantumSession request method ensures token."""
    mock_post.return_value.json.return_value = {"access_token": "test_token", "expires_in": 300}
    session = OpenQuantumSession(client_id="id", client_secret="secret")
    session.request("GET", "https://api.openquantum.com")
    assert session._token == "test_token"
    mock_super_request.assert_called_once()
    assert mock_super_request.call_args[1]["headers"]["Authorization"] == "Bearer test_token"


@patch("time.time")
def test_session_ensure_token_expired(mock_time):
    """Test _ensure_token when token is close to expiration."""
    session = OpenQuantumSession(client_id="id", client_secret="secret")
    session._token = "old_token"
    session._token_expires_at = 100
    mock_time.return_value = 90
    with patch.object(session, "_fetch_token") as mock_fetch:
        session._ensure_token()
        mock_fetch.assert_called_once()


def test_session_download_job_output_no_url():
    """Test download_job_output when output_url is missing."""
    session = OpenQuantumSession(client_id="id", client_secret="secret")
    with patch.object(session, "get_job", return_value={"id": "job_123", "output_data_url": None}):
        with pytest.raises(ResourceNotFoundError, match="Job output URL not available."):
            session.download_job_output("job_123")


@patch("requests.get")
def test_session_download_job_output_success(mock_get):
    """Test download_job_output success."""
    mock_get.return_value.json.return_value = {"00": 100}
    mock_get.return_value.raise_for_status.return_value = None
    session = OpenQuantumSession(client_id="id", client_secret="secret")
    with patch.object(
        session,
        "get_job",
        return_value={"id": "job_123", "output_data_url": "http://example.com/out"},
    ):
        res = session.download_job_output("job_123")
        assert res == {"00": 100}
        mock_get.assert_called_once_with("http://example.com/out", timeout=60)


@patch("time.time")
def test_session_wait_for_preparation_timeout(mock_time):
    """Test wait_for_preparation timeout."""
    session = OpenQuantumSession(client_id="id", client_secret="secret")
    with patch.object(session, "get_preparation_result", return_value={"status": "Pending"}):
        mock_time.side_effect = [0, 10, 30, 310]
        with patch("time.sleep"):
            with pytest.raises(TimeoutError, match="Job preparation timed out."):
                session.wait_for_preparation("prep_123", timeout=300)


def test_session_wait_for_preparation_failed():
    """Test wait_for_preparation failed state."""
    session = OpenQuantumSession(client_id="id", client_secret="secret")
    with patch.object(
        session, "get_preparation_result", return_value={"status": "Failed", "message": "Bad error"}
    ):
        with pytest.raises(ValueError, match="Job preparation failed: Bad error"):
            session.wait_for_preparation("prep_123")


def test_device_submit_no_orgs(provider):
    """Test submitting a job when user has no organizations."""
    provider.session.get_user_organizations.return_value = []
    device = provider.get_device("oq-sim")
    with pytest.raises(QbraidRuntimeError, match="Failed to connect to Open Quantum."):
        device.submit("OPENQASM 3.0; h q[0];")


def test_device_submit_empty_quote(provider):
    """Test submit when quote is empty."""
    provider.session.wait_for_preparation.return_value = []
    device = provider.get_device("oq-sim")
    with pytest.raises(
        ValueError, match="No valid execution plans or queue priorities found in quote."
    ):
        device.submit("OPENQASM 3.0; h q[0];")


def test_device_submit_plan_missing_priority(provider):
    """Test submit when execution plan exists but requested queue priority is not in it."""
    custom_quote = [
        {"execution_plan_id": "plan_1", "queue_priorities": [{"queue_priority_id": "prio_A"}]}
    ]
    provider.session.wait_for_preparation.return_value = custom_quote
    device = provider.get_device("oq-sim")
    with pytest.raises(ValueError, match="Queue priority 'prio_X' not found in selected plan."):
        device.submit(
            "OPENQASM 3.0; h q[0];", execution_plan_id="plan_1", queue_priority_id="prio_X"
        )


@patch("requests.put")
def test_session_api_methods(mock_put):
    """Test OpenQuantumSession various API methods."""
    session = OpenQuantumSession(client_id="id", client_secret="secret")

    with patch.object(session, "get") as mock_get:
        mock_get.return_value.json.return_value = {"id": "oq-sim"}
        assert session.get_backend_class_details("oq-sim") == {"id": "oq-sim"}

        mock_get.return_value.json.return_value = {"organizations": [{"id": "org1"}]}
        assert session.get_user_organizations() == [{"id": "org1"}]

        mock_get.return_value.json.return_value = {"status": "Pending"}
        assert session.get_preparation_result("prep_123") == {"status": "Pending"}

        mock_get.return_value.json.return_value = {"id": "job_123"}
        assert session.get_job("job_123") == {"id": "job_123"}

    with patch.object(session, "post") as mock_post:
        mock_post.return_value.json.return_value = {"id": "upload_123", "url": "http://upload"}
        assert session.upload_input(b"data") == "upload_123"
        mock_put.assert_called_once_with("http://upload", data=b"data", timeout=60)

        mock_post.return_value.json.return_value = {"id": "prep_123"}
        assert session.prepare_job({}) == {"id": "prep_123"}

        mock_post.return_value.json.return_value = {"id": "job_123"}
        assert session.create_job({}) == {"id": "job_123"}

    with patch.object(session, "delete") as mock_delete:
        mock_delete.return_value.raise_for_status.return_value = None
        session.cancel_job("job_123")
        mock_delete.assert_called_once()


def test_session_get_devices_pagination():
    """Test get_devices with pagination."""
    session = OpenQuantumSession(client_id="id", client_secret="secret")
    with patch.object(session, "get") as mock_get:
        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = {
            "backend_classes": [{"id": "1"}],
            "pagination": {"next_cursor": "cursor_1"},
        }
        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = {
            "backend_classes": [{"id": "2"}],
            "pagination": {"next_cursor": None},
        }
        mock_get.side_effect = [mock_response_1, mock_response_2]

        devices = session.get_devices()
        assert len(devices) == 2
        assert devices[0]["id"] == "1"
        assert devices[1]["id"] == "2"

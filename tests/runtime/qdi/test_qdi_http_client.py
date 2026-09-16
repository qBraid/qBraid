# Copyright 2026 qBraid
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

# pylint: disable=redefined-outer-name

"""
Unit tests for the QDI-over-HTTP client against the reference server's
REST binding, with the transport mocked.

"""

import json
from unittest.mock import MagicMock, patch

import pytest
from qbraid_core.exceptions import RequestsApiError
from qbraid_core.sessions import Session

from qbraid.runtime.qdi import QdiError, QdiHttpClient, QdiProvider, QdiStatus, QdiTaskStatus

from .conftest import DEMO_MOCK, QASM3_BELL

BASE_URL = "http://127.0.0.1:8000"


def _response(payload):
    response = MagicMock()
    response.json.return_value = payload
    return response


@pytest.fixture
def client():
    """An HTTP client with no token, as before the handshake."""
    return QdiHttpClient(BASE_URL)


def test_bearer_token_up_front():
    """A token given at construction is sent as a bearer on every request (spec §2.2)."""
    client = QdiHttpClient(BASE_URL + "/", token="valid-token")
    assert client.base_url == BASE_URL
    assert client.headers["Authorization"] == "Bearer valid-token"
    assert client.session.auth_headers == {"Authorization": "Bearer valid-token"}


def test_discover_path(client):
    """Discover is ``GET /qdi/v1/devices`` and returns the body unchanged."""
    with patch.object(Session, "request", return_value=_response({"devices": [DEMO_MOCK]})) as req:
        assert client.discover() == {"devices": [DEMO_MOCK]}
    req.assert_called_once_with("GET", "/qdi/v1/devices")


def test_authenticate_stores_access_token(client):
    """The ``access_token`` from the handshake becomes the bearer for later calls."""
    body = {"status": "authenticated", "token_type": "Bearer", "access_token": "valid-token"}
    with patch.object(Session, "request", return_value=_response(body)) as req:
        client.authenticate("mock_qdi_qubit_v1", {"token": "valid-token"})
    req.assert_called_once_with(
        "POST", "/qdi/v1/devices/mock_qdi_qubit_v1/authenticate", json={"token": "valid-token"}
    )
    assert client.token == "valid-token"
    assert client.headers["Authorization"] == "Bearer valid-token"
    # Masking relies on auth_headers being kept in sync.
    assert client.session.auth_headers["Authorization"] == "Bearer valid-token"


def test_send_body_and_task_id(client):
    """Send posts the payload as text with task_type, shots, and extensions."""
    body = {"task_id": "abc-123", "status": "submitted"}
    with patch.object(Session, "request", return_value=_response(body)) as req:
        task_id = client.send(
            "mock_qdi_qubit_v1",
            QASM3_BELL.encode("utf-8"),
            "openqasm3",
            shots=20,
            extensions={"transpiler_info": "level3"},
        )
    assert task_id == "abc-123"
    req.assert_called_once_with(
        "POST",
        "/qdi/v1/devices/mock_qdi_qubit_v1/tasks",
        json={
            "task_payload": QASM3_BELL,
            "task_type": "openqasm3",
            "shots": 20,
            "extensions": {"transpiler_info": "level3"},
        },
    )


def test_send_defaults_extensions_to_empty_object(client):
    """No extensions is sent as ``{}``, which is what the reference server expects."""
    with patch.object(Session, "request", return_value=_response({"task_id": "t"})) as req:
        client.send("mock_qdi_qubit_v1", b"OPENQASM 3.0;", "openqasm3")
    assert req.call_args.kwargs["json"]["extensions"] == {}


def test_send_rejects_binary_payload(client):
    """The binding carries JSON text; a non-UTF-8 payload is refused before the request."""
    with patch.object(Session, "request") as req:
        with pytest.raises(QdiError) as excinfo:
            client.send("mock_qdi_qubit_v1", b"\xff\xfe\x00BC", "qir")
    assert excinfo.value.status == QdiStatus.ERROR_UNSUPPORTED_FORMAT
    req.assert_not_called()


def test_monitor_maps_status_name(client):
    """Monitor turns the server's state name into the ``qdi_task_status`` integer."""
    body = {"task_id": "t", "status": "EXECUTING", "advisory_metadata": {"queue_position": 0}}
    with patch.object(Session, "request", return_value=_response(body)) as req:
        status, advisory = client.monitor("mock_qdi_qubit_v1", "t")
    req.assert_called_once_with("GET", "/qdi/v1/devices/mock_qdi_qubit_v1/tasks/t/status")
    assert status == int(QdiTaskStatus.EXECUTING)
    assert advisory == {"queue_position": 0}


def test_monitor_without_advisory(client):
    """A missing or null advisory block reads as an empty dict."""
    with patch.object(Session, "request", return_value=_response({"status": "QUEUED"})):
        assert client.monitor("d", "t") == (0, {})
    body = {"status": "QUEUED", "advisory_metadata": None}
    with patch.object(Session, "request", return_value=_response(body)):
        assert client.monitor("d", "t") == (0, {})


def test_monitor_rejects_non_qdi_state(client):
    """A state outside the five QDI names is an error, not a silent UNKNOWN."""
    with patch.object(Session, "request", return_value=_response({"status": "PAUSED"})):
        with pytest.raises(QdiError, match="'PAUSED'"):
            client.monitor("d", "t")


def test_receive_returns_json_payload(client):
    """Receive re-serializes the result so the payload is opaque text, as QDI defines it."""
    body = {"task_id": "t", "result_type": "counts", "result": {"00": 55, "11": 45}}
    with patch.object(Session, "request", return_value=_response(body)) as req:
        payload, result_type = client.receive("mock_qdi_qubit_v1", "t")
    req.assert_called_once_with("GET", "/qdi/v1/devices/mock_qdi_qubit_v1/tasks/t/results")
    assert result_type == "counts"
    assert json.loads(payload) == {"00": 55, "11": 45}


def test_estimate_path(client):
    """Estimate posts the same body shape as Send to ``/estimate``."""
    body = {"shots": 20, "shots_duration_sec": 0.03}
    with patch.object(Session, "request", return_value=_response(body)) as req:
        assert client.estimate_resources("d", b"OPENQASM 3.0;", "openqasm3", shots=20) == body
    assert req.call_args.args == ("POST", "/qdi/v1/devices/d/estimate")
    assert req.call_args.kwargs["json"]["shots"] == 20


@pytest.mark.parametrize(
    ("http_status", "qdi_status"),
    [
        (400, QdiStatus.ERROR_INVALID_ARGUMENT),
        (401, QdiStatus.ERROR_UNAUTHORIZED),
        (403, QdiStatus.ERROR_UNAUTHORIZED),
        (404, QdiStatus.ERROR_TASK_NOT_FOUND),
        (422, QdiStatus.ERROR_INVALID_ARGUMENT),
        (501, QdiStatus.ERROR_ESTIMATION_FAILED),
        (500, QdiStatus.ERROR_UNKNOWN),
        (None, QdiStatus.ERROR_CONNECTION_FAILED),
    ],
)
def test_http_errors_map_to_qdi_status(client, http_status, qdi_status):
    """HTTP failures become ``QdiError`` with the closest status code (spec §4)."""
    err = RequestsApiError("Authentication required.", status_code=http_status)
    with patch.object(Session, "request", side_effect=err):
        with pytest.raises(QdiError) as excinfo:
            client.discover()
    assert excinfo.value.status == qdi_status
    assert excinfo.value.operation == "discover"
    assert excinfo.value.__cause__ is err


def test_custom_api_prefix():
    """A server that mounts QDI elsewhere can be addressed with ``api_prefix``."""
    client = QdiHttpClient(BASE_URL, api_prefix="api/qdi/")
    with patch.object(Session, "request", return_value=_response({"devices": []})) as req:
        client.discover()
    req.assert_called_once_with("GET", "/api/qdi/devices")


def test_provider_over_http_full_lifecycle():
    """Provider + HTTP client: open Discover, handshake, run, result; transport mocked."""
    responses = {
        ("GET", "/qdi/v1/devices"): {"devices": [DEMO_MOCK]},
        ("POST", "/qdi/v1/devices/mock_qdi_qubit_v1/authenticate"): {
            "status": "authenticated",
            "token_type": "Bearer",
            "access_token": "valid-token",
        },
        ("POST", "/qdi/v1/devices/mock_qdi_qubit_v1/tasks"): {"task_id": "t-1"},
        ("GET", "/qdi/v1/devices/mock_qdi_qubit_v1/tasks/t-1/status"): {
            "status": "COMPLETED",
            "advisory_metadata": {},
        },
        ("GET", "/qdi/v1/devices/mock_qdi_qubit_v1/tasks/t-1/results"): {
            "result_type": "counts",
            "result": {"00": 10, "11": 10},
        },
    }

    def fake_request(_self, method, path, **_kwargs):
        return _response(responses[(method, path)])

    with patch.object(Session, "request", autospec=True, side_effect=fake_request):
        provider = QdiProvider(base_url=BASE_URL, credentials={"token": "valid-token"})
        device = provider.get_device("mock_qdi_qubit_v1")
        job = device.run(QASM3_BELL, shots=20)
        counts = job.result().data.get_counts()

    assert provider.client.headers["Authorization"] == "Bearer valid-token"
    assert counts == {"00": 10, "11": 10}

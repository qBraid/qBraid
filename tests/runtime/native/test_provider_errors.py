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

"""Device lookup failures retain the qBraid service's error information."""

# pylint: disable=redefined-outer-name

import json
from http import HTTPStatus
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from qbraid_core.exceptions import RequestsApiError
from qbraid_core.services.runtime import QuantumRuntimeClient, QuantumRuntimeServiceRequestError
from qbraid_core.sessions import QbraidSessionV1
from requests import ConnectionError as RequestsConnectionError
from requests import HTTPError, Response, Timeout
from requests.sessions import Session

from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.native import QbraidProvider

DEVICE_ID = "qbraid:qbraid:sim:qir-sv"


@pytest.fixture
def provider_transport(mock_client, monkeypatch):
    """Use the real core client/session, replacing only authentication and HTTP transport."""
    monkeypatch.setenv("DISABLE_CACHE", "1")
    with (
        patch.object(Session, "request") as transport,
        patch.object(
            QbraidSessionV1, "get_user_auth_metadata", return_value=mock_client._user_metadata
        ),
    ):
        transport.side_effect = AssertionError("Unexpected HTTP request")
        client = QuantumRuntimeClient(api_key="fake_api_key")
        yield QbraidProvider(client=client), transport


def response(status_code: int, data: dict[str, Any]) -> Response:
    """Build a requests response, with Retry-After when the response is rate-limited."""
    result = Response()
    result.status_code = status_code
    result.reason = HTTPStatus(status_code).phrase
    result.url = f"https://api.qbraid.com/devices/{DEVICE_ID}"
    result.headers["Content-Type"] = "application/json"
    if status_code == 429:
        result.headers["Retry-After"] = "30"
    result._content = json.dumps(data).encode()  # pylint: disable=protected-access
    return result


def lookup(provider: QbraidProvider, method: str):
    """Exercise both the single-device and device-list public methods."""
    return provider.get_device(DEVICE_ID) if method == "get_device" else provider.get_devices()


@pytest.mark.parametrize("method", ["get_device", "get_devices"])
@pytest.mark.parametrize("status_code", [401, 403, 429, 503])
def test_device_http_errors_keep_status_and_response(
    provider_transport, method, status_code
) -> None:
    """A rate limit or service failure must not be presented as a missing device (#1518)."""
    provider, transport = provider_transport
    message = (
        "Too many requests from user, please try again later"
        if status_code == 429
        else HTTPStatus(status_code).phrase
    )
    data = {"message": message}
    if status_code == 429:
        data["error"] = {"code": "TOO_MANY_REQUESTS"}
    http_response = response(status_code, data)
    transport.side_effect = None
    transport.return_value = http_response

    with pytest.raises(QuantumRuntimeServiceRequestError) as raised:
        lookup(provider, method)

    assert raised.value.status_code == status_code
    assert message in str(raised.value)
    api_error = raised.value.__cause__
    assert isinstance(api_error, RequestsApiError)
    assert isinstance(api_error.__cause__, HTTPError)
    assert api_error.__cause__.response is http_response
    if status_code == 429:
        assert api_error.__cause__.response.headers["Retry-After"] == "30"
    transport.assert_called_once()


@pytest.mark.parametrize("method", ["get_device", "get_devices"])
@pytest.mark.parametrize("error_type", [RequestsConnectionError, Timeout])
def test_device_transport_failures_remain_service_errors(
    provider_transport, method, error_type
) -> None:
    """A request with no HTTP response is not evidence that the device is missing."""
    provider, transport = provider_transport
    failure = error_type("Request did not reach the service")
    transport.side_effect = failure
    with pytest.raises(QuantumRuntimeServiceRequestError) as raised:
        lookup(provider, method)
    assert raised.value.status_code is None
    assert raised.value.__cause__.__cause__ is failure


def test_single_device_404_is_reported_as_missing(provider_transport) -> None:
    """An actual device 404 retains the SDK's missing-device exception and cause."""
    provider, transport = provider_transport
    transport.side_effect = None
    transport.return_value = response(404, {"message": "Device not found"})
    with pytest.raises(ResourceNotFoundError, match="not found") as raised:
        provider.get_device(DEVICE_ID)
    assert isinstance(raised.value.__cause__, QuantumRuntimeServiceRequestError)
    assert raised.value.__cause__.status_code == 404


def test_device_list_404_remains_a_service_error(provider_transport) -> None:
    """A missing list endpoint is not an empty device search result."""
    provider, transport = provider_transport
    transport.side_effect = None
    transport.return_value = response(404, {"message": "Endpoint not found"})
    with pytest.raises(QuantumRuntimeServiceRequestError) as raised:
        provider.get_devices()
    assert raised.value.status_code == 404


def test_empty_device_list_still_reports_no_matching_devices(provider_transport) -> None:
    """A successful empty response still uses the existing no-results error."""
    provider, transport = provider_transport
    transport.side_effect = None
    transport.return_value = response(200, {"data": []})
    with pytest.raises(ResourceNotFoundError, match="No devices found"):
        provider.get_devices()


def test_invalid_device_payload_remains_a_validation_error(provider_transport) -> None:
    """Invalid service data must not masquerade as a device 404."""
    provider, transport = provider_transport
    transport.side_effect = None
    transport.return_value = response(200, {"data": {"qrn": DEVICE_ID}})
    with pytest.raises(ValidationError):
        provider.get_device(DEVICE_ID)

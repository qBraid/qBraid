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

"""
Unit tests for the AQT provider, the ``AQTSession`` arnica HTTP client, and non-interactive
access-token resolution.

``aqt-connector`` is a real installed dependency: the session's HTTP transport is mocked and its
auth functions are monkeypatched on the ``qbraid.runtime.aqt.provider`` module. No network access
occurs.
"""

from __future__ import annotations

import types
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
from qbraid_core.exceptions import RequestsApiError

from qbraid.programs import ProgramSpec
from qbraid.runtime.aqt import AQTDevice, AQTProvider, AQTSession
from qbraid.runtime.aqt.provider import _resolve_access_token
from qbraid.runtime.exceptions import ResourceNotFoundError

# ---------------------------------------------------------------------------
# provider
# ---------------------------------------------------------------------------


def test_build_profile_targets_aqt_alias():
    """The profile's ``ProgramSpec`` targets the ``aqt`` alias, with arnica routing extras."""
    profile = AQTProvider._build_profile(
        {"id": "ibex", "type": "device", "available_qubits": 12}, "aqt"
    )
    assert profile.device_id == "aqt/ibex"
    assert profile.simulator is False
    assert profile.num_qubits == 12
    assert profile.provider_name == "AQT"
    assert profile.get("aqt_workspace_id") == "aqt"
    assert profile.get("aqt_resource_id") == "ibex"
    assert profile.get("aqt_resource_type") == "device"

    spec = profile.program_spec
    assert isinstance(spec, ProgramSpec)
    assert spec.alias == "aqt"


def test_get_devices():
    """``get_devices`` builds one ``AQTDevice`` per resource across visible workspaces."""
    provider = AQTProvider(access_token="tok")
    provider.session.get_workspaces = MagicMock(
        return_value=[{"id": "default", "resources": [{"id": "sim1", "type": "simulator"}]}]
    )
    provider.session.get_resource = MagicMock(
        return_value={"id": "sim1", "type": "simulator", "available_qubits": 20, "status": "online"}
    )
    devices = provider.get_devices()
    assert len(devices) == 1
    assert isinstance(devices[0], AQTDevice)
    assert devices[0].id == "default/sim1"


def test_get_device():
    """``get_device`` resolves a ``"<workspace>/<resource>"`` id to an ``AQTDevice``."""
    provider = AQTProvider(access_token="tok")
    provider.session.get_resource = MagicMock(
        return_value={"id": "sim1", "type": "simulator", "available_qubits": 20}
    )
    device = provider.get_device("default/sim1")
    assert isinstance(device, AQTDevice)
    assert device.id == "default/sim1"
    assert device.workspace_id == "default"
    assert device.resource_id == "sim1"


def test_get_device_invalid_id():
    """A device id without a ``/`` separator raises ``ResourceNotFoundError``."""
    provider = AQTProvider(access_token="tok")
    with pytest.raises(ResourceNotFoundError):
        provider.get_device("no-separator")


def test_provider_hash():
    """``AQTProvider`` is hashable (keyed on token + base url)."""
    provider = AQTProvider(access_token="tok")
    assert isinstance(hash(provider), int)


# ---------------------------------------------------------------------------
# AQTSession HTTP
# ---------------------------------------------------------------------------


def _mock_http_session() -> AQTSession:
    """A real ``AQTSession`` with its ``requests`` transport (get/post/delete) mocked out."""
    session = AQTSession(access_token="tok")
    session.get = MagicMock()
    session.post = MagicMock()
    session.delete = MagicMock()
    return session


def test_session_base_url_and_token():
    """The base url appends ``/v1`` to the arnica root, and the token is exposed."""
    session = AQTSession(access_token="tok", arnica_url="https://example.test/api")
    assert session.base_url == "https://example.test/api/v1"
    assert session.access_token == "tok"


def test_session_base_url_strips_duplicate_v1():
    """A URL already ending in ``/v1`` is normalized rather than doubled."""
    session = AQTSession(access_token="tok", arnica_url="https://example.test/api/v1")
    assert session.base_url == "https://example.test/api/v1"


def test_session_explicit_token_skips_resolution(monkeypatch):
    """An explicit ``access_token`` short-circuits ``_resolve_access_token`` entirely."""

    def _fail(*_args, **_kwargs):
        raise AssertionError("_resolve_access_token should not be called for an explicit token")

    monkeypatch.setattr("qbraid.runtime.aqt.provider._resolve_access_token", _fail)
    session = AQTSession(access_token="explicit-token")
    assert session.access_token == "explicit-token"


def test_session_http_methods():
    """Each session helper hits the right route and returns the decoded JSON body."""
    session = _mock_http_session()

    session.get.return_value.json.return_value = [{"id": "w"}]
    assert session.get_workspaces() == [{"id": "w"}]
    session.get.assert_called_with("/workspaces")

    session.get.return_value.json.return_value = {"id": "sim1", "status": "online"}
    assert session.get_resource("sim1")["status"] == "online"

    session.post.return_value.json.return_value = {"job": {"job_id": "j1"}}
    assert session.submit_job("ws", "res", {"payload": {}}) == {"job": {"job_id": "j1"}}

    session.get.return_value.json.return_value = {"response": {"status": "finished"}}
    assert session.get_result("j1")["response"]["status"] == "finished"

    session.cancel_job("j1")
    session.delete.assert_called_once_with("/jobs/j1")


def _requests_api_error(status_code: int) -> RequestsApiError:
    """A ``RequestsApiError`` chained from an ``HTTPError`` whose response carries a status code."""
    cause = requests.HTTPError("http error")
    cause.response = types.SimpleNamespace(status_code=status_code)
    error = RequestsApiError("request failed")
    error.__cause__ = cause
    return error


def test_session_get_resource_404_maps_to_not_found():
    """A genuine 404 from arnica is surfaced as ``ResourceNotFoundError``."""
    session = _mock_http_session()
    session.get.side_effect = _requests_api_error(404)
    with pytest.raises(ResourceNotFoundError):
        session.get_resource("missing")


def test_session_get_resource_non_404_propagates():
    """A non-404 (e.g. 401 auth) ``RequestsApiError`` propagates instead of mapping to not-found."""
    session = _mock_http_session()
    session.get.side_effect = _requests_api_error(401)
    with pytest.raises(RequestsApiError):
        session.get_resource("forbidden")


# ---------------------------------------------------------------------------
# auth resolution
# ---------------------------------------------------------------------------


class _FakeArnicaConfig:
    """Stand-in for ``aqt_connector.ArnicaConfig`` mirroring the fields the resolver touches."""

    def __init__(self) -> None:
        self.client_id = None
        self.client_secret = None
        self.store_access_token = True
        # Mirror the real defaults: audience/arnica_url point at production.
        self.arnica_url = "https://arnica.aqt.eu/api"
        self.oidc_config = types.SimpleNamespace(audience="https://arnica.aqt.eu/api")


def _patch_arnica(monkeypatch, *, stored=None, cc_token="cc-token") -> dict[str, Any]:
    """Monkeypatch the real ``aqt_connector`` auth functions on the provider module.

    Returns a dict whose ``"config"`` key is populated with the ``ArnicaConfig`` passed to
    ``ArnicaApp`` once ``_resolve_access_token`` runs.
    """
    captured: dict[str, Any] = {"config": None}

    def fake_arnica_app(config):
        captured["config"] = config
        return types.SimpleNamespace(config=config)

    monkeypatch.setattr("qbraid.runtime.aqt.provider.ArnicaConfig", _FakeArnicaConfig)
    monkeypatch.setattr("qbraid.runtime.aqt.provider.ArnicaApp", fake_arnica_app)
    monkeypatch.setattr("qbraid.runtime.aqt.provider.get_access_token", lambda app: stored)
    monkeypatch.setattr("qbraid.runtime.aqt.provider.log_in", lambda app: cc_token)
    return captured


def test_resolve_token_stored_session(monkeypatch):
    """A stored/refreshed aqt-connector session token is returned when present."""
    monkeypatch.delenv("AQT_CLIENT_ID", raising=False)
    monkeypatch.delenv("AQT_CLIENT_SECRET", raising=False)
    _patch_arnica(monkeypatch, stored="stored")
    assert _resolve_access_token() == "stored"


def test_resolve_token_client_credentials_from_env(monkeypatch):
    """With no stored token, ``AQT_CLIENT_ID``/``AQT_CLIENT_SECRET`` drive the client-credentials
    flow."""
    monkeypatch.setenv("AQT_CLIENT_ID", "cid")
    monkeypatch.setenv("AQT_CLIENT_SECRET", "csecret")
    captured = _patch_arnica(monkeypatch, stored=None, cc_token="cc")

    assert _resolve_access_token() == "cc"
    assert captured["config"].client_id == "cid"
    assert captured["config"].client_secret == "csecret"


def test_resolve_token_disables_persistence(monkeypatch):
    """The resolver disables token persistence (``store_access_token = False``)."""
    monkeypatch.setenv("AQT_CLIENT_ID", "cid")
    monkeypatch.setenv("AQT_CLIENT_SECRET", "csecret")
    captured = _patch_arnica(monkeypatch, stored=None, cc_token="cc")

    _resolve_access_token()
    assert captured["config"].store_access_token is False


def test_resolve_token_applies_audience(monkeypatch):
    """A non-default audience (e.g. staging) is applied to both the request and the verifier."""
    monkeypatch.setenv("AQT_CLIENT_ID", "cid")
    monkeypatch.setenv("AQT_CLIENT_SECRET", "csecret")
    captured = _patch_arnica(monkeypatch, stored=None, cc_token="cc")

    staging = "https://arnica-staging.aqt.eu/api"
    assert _resolve_access_token(audience=staging) == "cc"
    assert captured["config"].arnica_url == staging
    assert captured["config"].oidc_config.audience == staging
    assert captured["config"].store_access_token is False


def test_resolve_token_none_available_raises(monkeypatch):
    """With no token and no client credentials, resolution raises ``ValueError``."""
    monkeypatch.delenv("AQT_CLIENT_ID", raising=False)
    monkeypatch.delenv("AQT_CLIENT_SECRET", raising=False)
    _patch_arnica(monkeypatch, stored=None)
    with pytest.raises(ValueError, match="No AQT access token"):
        _resolve_access_token()

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
Unit tests for the QPerfect (MIMIQ) authentication flow.

Covers the order QPerfect documents at
https://docs.qperfect.io/mimiqcircuits-python/manual/remote_execution.html — refresh token first,
account credentials otherwise — plus the expiry behaviour that motivates it: MIMIQ tokens last
about a day, so a rejected token must fall back to a credentials login rather than fail the call.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from qbraid.runtime.qperfect.client import (
    PASSWORD_ENV_VAR,
    TOKEN_ENV_VAR,
    URL_ENV_VAR,
    USERNAME_ENV_VAR,
    build_connection,
    resolve_account,
    resolve_url,
)

_ENV_VARS = (TOKEN_ENV_VAR, USERNAME_ENV_VAR, PASSWORD_ENV_VAR, URL_ENV_VAR)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Start every test from an unconfigured environment, whatever the developer has set."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def mimiq_connection():
    """Patch ``MimiqConnection`` and hand back the instance ``build_connection`` will use."""
    with patch("qbraid.runtime.qperfect.client.MimiqConnection") as ctor:
        instance = MagicMock()
        instance.connection = MagicMock()
        instance.connection.refresh_token = "rotated-token"
        ctor.return_value = instance
        yield ctor, instance


def test_explicit_token_authenticates_with_connect_token(mimiq_connection):
    """A token passed by the caller is used verbatim, without an account login."""
    _, instance = mimiq_connection
    build_connection("caller-token")
    instance.connection.connectToken.assert_called_once_with("caller-token")
    instance.connection.connectUser.assert_not_called()


def test_env_token_is_used_when_no_argument(monkeypatch, mimiq_connection):
    """``QPERFECT_API_TOKEN`` supplies the token when the caller passes none."""
    monkeypatch.setenv(TOKEN_ENV_VAR, "env-token")
    _, instance = mimiq_connection
    build_connection()
    instance.connection.connectToken.assert_called_once_with("env-token")


def test_credentials_used_when_no_token(monkeypatch, mimiq_connection):
    """With no token anywhere, the account login runs."""
    monkeypatch.setenv(USERNAME_ENV_VAR, "user@example.com")
    monkeypatch.setenv(PASSWORD_ENV_VAR, "secret")
    _, instance = mimiq_connection
    build_connection()
    instance.connection.connectUser.assert_called_once_with("user@example.com", "secret")
    instance.connection.connectToken.assert_not_called()


@pytest.mark.usefixtures("mimiq_connection")
def test_credentials_login_publishes_refresh_token(monkeypatch):
    """The token the login mints is kept, so the next connection in this process reuses it."""
    monkeypatch.setenv(USERNAME_ENV_VAR, "user@example.com")
    monkeypatch.setenv(PASSWORD_ENV_VAR, "secret")
    build_connection()
    assert os.environ[TOKEN_ENV_VAR] == "rotated-token"


def test_expired_token_falls_back_to_credentials(monkeypatch, mimiq_connection):
    """A day-old token must not take down a service that also has working credentials.

    Reproduces the expiry MIMIQ documents: tokens live about a day, so the stored one goes stale
    on its own. Without this fallback the provider would start failing roughly daily.
    """
    monkeypatch.setenv(TOKEN_ENV_VAR, "stale-token")
    monkeypatch.setenv(USERNAME_ENV_VAR, "user@example.com")
    monkeypatch.setenv(PASSWORD_ENV_VAR, "secret")
    _, instance = mimiq_connection
    instance.connection.connectToken.side_effect = ConnectionError("Authentication failed.")

    build_connection()

    instance.connection.connectToken.assert_called_once_with("stale-token")
    instance.connection.connectUser.assert_called_once_with("user@example.com", "secret")


def test_rejected_token_raises_when_no_credentials(monkeypatch, mimiq_connection):
    """With nothing to fall back to, the vendor error surfaces instead of being swallowed."""
    monkeypatch.setenv(TOKEN_ENV_VAR, "stale-token")
    _, instance = mimiq_connection
    instance.connection.connectToken.side_effect = ConnectionError("Authentication failed.")

    with pytest.raises(ConnectionError, match="Authentication failed."):
        build_connection()


def test_no_credentials_at_all_raises():
    """An unconfigured environment names both accepted configurations."""
    with pytest.raises(ValueError, match=USERNAME_ENV_VAR):
        build_connection()


@pytest.mark.parametrize("present, missing", [(USERNAME_ENV_VAR, PASSWORD_ENV_VAR)])
def test_half_a_credential_pair_raises(monkeypatch, present, missing):
    """Half a pair is a misconfiguration, not a reason to fall through to another method."""
    monkeypatch.setenv(present, "value")
    with pytest.raises(ValueError, match=missing):
        resolve_account()


def test_resolve_account_returns_none_when_unset():
    """No credentials configured is a normal state, not an error."""
    assert resolve_account() is None


def test_resolve_url_prefers_argument_then_env(monkeypatch):
    """Explicit URL wins; otherwise the env var; otherwise the public cloud."""
    monkeypatch.setenv(URL_ENV_VAR, "https://env.example")
    assert resolve_url("https://arg.example") == "https://arg.example"
    assert resolve_url() == "https://env.example"
    monkeypatch.delenv(URL_ENV_VAR)
    assert resolve_url().startswith("http")


def test_second_connection_reuses_the_published_token(monkeypatch, mimiq_connection):
    """The runtime API's flow: log in once with credentials, then reuse the minted token.

    Each vendor call builds its own provider, so this is what spares every later call a full
    account login. No token needs to be passed in — the first login publishes it.
    """
    monkeypatch.setenv(USERNAME_ENV_VAR, "user@example.com")
    monkeypatch.setenv(PASSWORD_ENV_VAR, "secret")
    _, instance = mimiq_connection

    build_connection()  # first call: no token anywhere, so credentials
    build_connection()  # second call: picks up the published token

    instance.connection.connectUser.assert_called_once_with("user@example.com", "secret")
    instance.connection.connectToken.assert_called_once_with("rotated-token")


def test_rotation_race_falls_back_instead_of_failing(monkeypatch, mimiq_connection):
    """Concurrent workers sharing one token can lose a rotation race; that must not fail a job.

    ``connectToken`` rotates the refresh token server-side, so a parallel worker's copy goes
    stale. The credentials fallback turns that into one extra login rather than an error.
    """
    monkeypatch.setenv(TOKEN_ENV_VAR, "token-rotated-by-another-worker")
    monkeypatch.setenv(USERNAME_ENV_VAR, "user@example.com")
    monkeypatch.setenv(PASSWORD_ENV_VAR, "secret")
    _, instance = mimiq_connection
    instance.connection.connectToken.side_effect = ConnectionError("Authentication failed.")

    assert build_connection() is instance
    instance.connection.connectUser.assert_called_once_with("user@example.com", "secret")

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
Unit tests for the QPerfect (MIMIQ) provider.

"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest
import requests
from mimiqcircuits import MimiqConnection

from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.qperfect import QPerfectDevice, QPerfectProvider


def test_construction_does_not_require_credentials(monkeypatch):
    """Building a provider never authenticates, so it works with nothing configured."""
    for var in ("QPERFECT_API_TOKEN", "QPERFECT_USERNAME", "QPERFECT_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    assert QPerfectProvider().get_device("mimiq-emulator") is not None


def test_connection_requires_credentials(monkeypatch):
    """Credentials are resolved on first connection use, and their absence raises there."""
    for var in ("QPERFECT_API_TOKEN", "QPERFECT_USERNAME", "QPERFECT_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValueError, match="QPERFECT_USERNAME"):
        _ = QPerfectProvider().connection


def test_get_devices(provider):
    """A single MIMIQ emulator device is exposed."""
    devices = provider.get_devices()
    assert [device.id for device in devices] == ["mimiq-emulator"]
    assert all(isinstance(device, QPerfectDevice) for device in devices)


def test_get_device(provider):
    """The emulator device advertises no qubit cap, leaving the limit to MIMIQ."""
    device = provider.get_device("mimiq-emulator")
    assert device.id == "mimiq-emulator"
    assert device.num_qubits is None


def test_get_device_unknown(provider):
    """An unknown device id raises ResourceNotFoundError."""
    with pytest.raises(ResourceNotFoundError):
        provider.get_device("nonexistent")


def test_program_spec_targets_mimiqcircuits(provider):
    """The device profile accepts the native ``mimiqcircuits`` circuit format."""
    assert provider.get_device("mimiq-emulator").profile.program_spec.alias == "mimiqcircuits"


def test_provider_is_hashable(provider):
    """The provider is hashable (it is cached by qBraid)."""
    assert isinstance(hash(provider), int)


def _connection_with_dead_refresher() -> MimiqConnection:
    """A real MIMIQ connection that authenticated once and whose token refresher has since died.

    mimiqlink's refresher loop has no error handling, so a single failed token refresh (a TLS
    EOF from mimiq.qperfect.io, for example) ends the thread, and ``isOpen()`` is False from then
    on even though the access token is still set.
    """
    connection = MimiqConnection("https://mimiq.qperfect.invalid")
    finished = threading.Thread(target=lambda: None)
    finished.start()
    finished.join()
    connection.connection.refresher_task = finished
    connection.connection.access_token = "stale-access-token"
    return connection


def test_connection_rebuilds_when_refresher_died(monkeypatch, mock_connection):
    """A connection whose refresher died is replaced on next use, so the device recovers."""
    monkeypatch.setattr(
        "qbraid.runtime.qperfect.provider.build_connection", lambda *args, **kwargs: mock_connection
    )
    provider = QPerfectProvider(token="fake-token")
    provider._connection = _connection_with_dead_refresher()  # pylint: disable=protected-access

    assert provider.get_device("mimiq-emulator").status() == DeviceStatus.ONLINE
    assert provider.connection is mock_connection


def test_open_connection_is_reused(monkeypatch, provider, mock_connection):
    """An open connection is kept: rebuilding it would cost a login and a refresher thread."""

    def fail_build(*args, **kwargs):
        raise AssertionError("an open connection must not be rebuilt")

    monkeypatch.setattr("qbraid.runtime.qperfect.provider.build_connection", fail_build)
    assert provider.connection is mock_connection


def test_concurrent_rebuild_logs_in_once(monkeypatch, mock_connection):
    """Callers that find the connection closed at the same time share one new login.

    Each login starts a refresher thread that runs for the life of the process, so a rebuild per
    caller would leave all but the last connection unreachable and still calling MIMIQ.
    """
    logins = []

    def slow_login(*_args, **_kwargs):
        time.sleep(0.05)
        logins.append(1)
        return mock_connection

    monkeypatch.setattr("qbraid.runtime.qperfect.provider.build_connection", slow_login)
    provider = QPerfectProvider(token="fake-token")
    provider._connection = _connection_with_dead_refresher()  # pylint: disable=protected-access

    with ThreadPoolExecutor(max_workers=8) as pool:
        connections = list(pool.map(lambda _: provider.connection, range(8)))

    assert len(logins) == 1
    assert all(connection is mock_connection for connection in connections)


def _logged_in(mock_connection):
    """Give the mocked connection the refresher state a real login leaves behind."""
    mock_connection.connection.refresher_lock = threading.Lock()
    mock_connection.connection.refresher_stop = False
    return mock_connection


def test_invalidate_connection_logs_in_again_and_stops_the_refresher(monkeypatch, mock_connection):
    """A session MIMIQ rejects while it still reports open is replaced on next access."""
    logins = []

    def login(*_args, **_kwargs):
        logins.append(1)
        return MagicMock()

    monkeypatch.setattr("qbraid.runtime.qperfect.provider.build_connection", login)
    provider = QPerfectProvider(token="fake-token")
    rejected = _logged_in(mock_connection)
    provider._connection = rejected  # pylint: disable=protected-access

    provider.invalidate_connection(rejected)

    assert rejected.connection.refresher_stop
    assert provider.connection is not rejected
    assert len(logins) == 1


def test_invalidate_connection_ignores_a_replaced_connection(monkeypatch, mock_connection):
    """A failure on a connection already replaced leaves the new one alone, costing no login."""

    def fail_build(*args, **kwargs):
        raise AssertionError("the current connection must not be discarded")

    monkeypatch.setattr("qbraid.runtime.qperfect.provider.build_connection", fail_build)
    provider = QPerfectProvider(token="fake-token")
    current = _logged_in(mock_connection)
    provider._connection = current  # pylint: disable=protected-access

    provider.invalidate_connection(MagicMock())

    assert provider.connection is current
    assert not current.connection.refresher_stop


def test_invalidate_connection_without_argument_discards_the_current_one(mock_connection):
    """``None`` discards whatever connection is current."""
    provider = QPerfectProvider(token="fake-token")
    current = _logged_in(mock_connection)
    provider._connection = current  # pylint: disable=protected-access

    provider.invalidate_connection()

    assert provider._connection is None  # pylint: disable=protected-access
    assert current.connection.refresher_stop


def test_token_only_provider_logs_in_again_with_the_rotated_token(monkeypatch, mock_connection):
    """After an invalidation, the next login uses the refresh token MIMIQ rotated to.

    MIMIQ rotates the refresh token every 15 minutes, so the one the provider was built with has
    stopped working by then. With no credentials to fall back to, reusing it left the provider
    disconnected for the life of the process.
    """
    tokens = []

    def login(token, **_kwargs):
        tokens.append(token)
        return MagicMock()

    monkeypatch.setattr("qbraid.runtime.qperfect.provider.build_connection", login)
    provider = QPerfectProvider(token="original-token")
    current = _logged_in(mock_connection)
    current.connection.refresh_token = "rotated-token"
    provider._connection = current  # pylint: disable=protected-access

    provider.invalidate_connection(current)
    _ = provider.connection

    assert tokens == ["rotated-token"]


def test_closed_connection_is_rebuilt_with_the_rotated_token(monkeypatch, mock_connection):
    """A connection whose refresher died is replaced using its latest refresh token."""
    tokens = []

    def login(token, **_kwargs):
        tokens.append(token)
        return mock_connection

    monkeypatch.setattr("qbraid.runtime.qperfect.provider.build_connection", login)
    provider = QPerfectProvider(token="original-token")
    dead = _connection_with_dead_refresher()
    dead.connection.refresh_token = "rotated-token"
    provider._connection = dead  # pylint: disable=protected-access

    _ = provider.connection

    assert tokens == ["rotated-token"]


def test_mimiqlink_internals_the_provider_relies_on():
    """Pin the mimiqlink attributes the SDK reaches into, so an upstream rename fails here.

    A renamed stop flag would not raise: setting it would add a new attribute, and every
    invalidation would leave a refresher thread calling MIMIQ for the life of the process.
    """
    link = MimiqConnection("http://127.0.0.1:1").connection
    assert isinstance(link.session, requests.Session)
    assert hasattr(link.refresher_lock, "acquire")
    assert link.refresher_stop is False

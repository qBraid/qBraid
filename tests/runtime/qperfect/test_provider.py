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

import pytest
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
    """The emulator device advertises the largest per-algorithm qubit reach."""
    device = provider.get_device("mimiq-emulator")
    assert device.id == "mimiq-emulator"
    assert device.num_qubits == 256


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

    def slow_login(*args, **kwargs):
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

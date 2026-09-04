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

import pytest

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

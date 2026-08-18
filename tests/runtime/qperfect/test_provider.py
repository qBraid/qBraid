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


def test_requires_token(monkeypatch):
    """Constructing a provider without a token (arg or env var) raises."""
    monkeypatch.delenv("QPERFECT_API_TOKEN", raising=False)
    with pytest.raises(ValueError):
        QPerfectProvider()


def test_token_from_env(monkeypatch):
    """The token falls back to the QPERFECT_API_TOKEN environment variable."""
    monkeypatch.setenv("QPERFECT_API_TOKEN", "env-token")
    assert QPerfectProvider()._token == "env-token"


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

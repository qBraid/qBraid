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

# pylint: disable=redefined-outer-name,missing-class-docstring,missing-function-docstring
"""
Unit tests for the deprecated ``sdk`` names of the Pasqal provider, device and job.

"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytest.importorskip("pasqal_cloud")
pytest.importorskip("pulser")

# pylint: disable=wrong-import-position
from qbraid.runtime.pasqal import PasqalJob, PasqalProvider  # noqa: E402
from qbraid.runtime.pasqal.provider import PasqalSession  # noqa: E402


@pytest.fixture
def mock_client(monkeypatch):
    """A stand-in ``pasqal_cloud`` client, with an empty device catalog."""
    monkeypatch.setattr(PasqalSession, "get_device_records", lambda self: {})
    client = MagicMock(name="PasqalCloudClient")
    client.project_id = "proj-1"
    client._client.endpoints.core = "https://apis.pasqal.cloud/core-fast"
    return client


class TestDeprecatedSdkAlias:
    """``sdk`` was renamed ``client``; the released ``sdk`` names still work, with a warning."""

    def test_provider(self, mock_client):
        with pytest.warns(DeprecationWarning, match="PasqalProvider's `sdk` is deprecated"):
            provider = PasqalProvider(sdk=mock_client)
        assert provider.client is mock_client
        with pytest.warns(DeprecationWarning, match="use `client`"):
            assert provider.sdk is mock_client

    def test_device(self, mock_client):
        device = PasqalProvider(client=mock_client).get_device("EMU_FREE")
        assert device.client is mock_client
        with pytest.warns(DeprecationWarning, match="PasqalDevice's `sdk` is deprecated"):
            assert device.sdk is mock_client

    def test_job(self, mock_client):
        with pytest.warns(DeprecationWarning, match="PasqalJob's `sdk` is deprecated"):
            job = PasqalJob(job_id="batch-1", sdk=mock_client)
        assert job.client is mock_client
        with pytest.warns(DeprecationWarning, match="use `client`"):
            assert job.sdk is mock_client

    def test_positional_client_is_unchanged(self, mock_client):
        """The fifth positional argument, once ``sdk``, is now ``client``: no call breaks."""
        provider = PasqalProvider(None, None, None, None, mock_client)
        assert provider.client is mock_client

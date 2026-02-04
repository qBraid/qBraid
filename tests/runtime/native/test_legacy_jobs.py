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
Unit tests for QbraidProvider legacy job methods:
    download_legacy_jobs

"""

import json
import os
import shutil
import zipfile
from unittest.mock import MagicMock, patch

import pytest
from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError

from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.native import QbraidProvider

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


SAMPLE_JOBS = [
    {
        "qbraidJobId": "device_a-jovyan-qjob-aaa",
        "qbraidDeviceId": "device_a",
        "provider": "ProviderX",
        "qbraidStatus": "COMPLETED",
        "createdAt": "2025-06-15T10:30:00.123Z",
        "timeStamps": {"createdAt": "2025-06-15T10:30:00.123Z"},
        "tags": {"env": "prod", "team": "alpha"},
    },
    {
        "qbraidJobId": "device_b-jovyan-qjob-bbb",
        "qbraidDeviceId": "device_b",
        "provider": "ProviderY",
        "qbraidStatus": "FAILED",
        "createdAt": "2025-06-16T08:00:00.000Z",
        "timeStamps": {"createdAt": "2025-06-16T08:00:00.000Z"},
        "tags": {"env": "staging"},
    },
    {
        "qbraidJobId": "device_a-jovyan-qjob-ccc",
        "qbraidDeviceId": "device_a",
        "provider": "providerx",
        "qbraidStatus": "RUNNING",
        "createdAt": "2025-06-14T12:00:00.000Z",
        "timeStamps": {"createdAt": "2025-06-14T12:00:00.000Z"},
        "tags": {"env": "prod"},
    },
]


@pytest.fixture
def mock_client():
    """QuantumClient stand-in with a controllable session.get mock."""
    client = MagicMock()
    client.session = MagicMock()
    return client


@pytest.fixture
def provider(mock_client):
    """QbraidProvider wired to the mock client."""
    return QbraidProvider(client=mock_client)


@pytest.fixture
def legacy_json_file(tmp_path):
    """Write SAMPLE_JOBS to a .json file and return its path."""
    path = str(tmp_path / ".old_jobs.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_JOBS, f)
    return path


@pytest.fixture
def legacy_zip_file(tmp_path):
    """Create a zip archive containing .old_jobs.json from SAMPLE_JOBS.

    Returns the path to the zip file.
    """
    json_content = json.dumps(SAMPLE_JOBS).encode("utf-8")
    zip_path = str(tmp_path / "archive.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(".old_jobs.json", json_content)
    return zip_path


def _success_response(url: str) -> MagicMock:
    """Return a mock response that yields a signed-URL payload."""
    resp = MagicMock()
    resp.json.return_value = {"success": True, "data": {"url": url}}
    return resp


# ---------------------------------------------------------------------------
# download_legacy_jobs — happy path
# ---------------------------------------------------------------------------


class TestDownloadLegacyJobsHappyPath:
    """Tests for the successful execution path of download_legacy_jobs."""

    def test_downloads_and_extracts_to_default_path(
        self, provider, mock_client, legacy_zip_file, tmp_path
    ):
        """Zip is downloaded, extracted to dest_path, zip is removed, path is returned."""
        dest = str(tmp_path / ".old_jobs.json")
        mock_client.session.get.return_value = _success_response("http://fake-url/archive.zip")

        with patch("qbraid.runtime.native.provider.urllib.request.urlretrieve") as mock_retrieve:
            mock_retrieve.side_effect = lambda _, dest_zip: shutil.copy(legacy_zip_file, dest_zip)

            with pytest.warns(DeprecationWarning, match="download_legacy_jobs"):
                result = provider.download_legacy_jobs(dest_path=dest)

        assert result == dest
        assert os.path.exists(dest)
        assert not os.path.exists(dest + ".zip")  # zip cleaned up

        with open(dest, "r", encoding="utf-8") as f:
            assert json.load(f) == SAMPLE_JOBS

    # pylint: disable-next=too-many-arguments
    def test_uses_cwd_as_default_dest_path(
        self, provider, mock_client, legacy_zip_file, tmp_path, monkeypatch
    ):
        """When dest_path is None the file lands in cwd as .old_jobs.json."""
        monkeypatch.chdir(tmp_path)
        mock_client.session.get.return_value = _success_response("http://fake-url/archive.zip")

        with patch("qbraid.runtime.native.provider.urllib.request.urlretrieve") as mock_retrieve:
            mock_retrieve.side_effect = lambda _, dest_zip: shutil.copy(legacy_zip_file, dest_zip)

            with pytest.warns(DeprecationWarning):
                result = provider.download_legacy_jobs()

        expected = os.path.join(str(tmp_path), ".old_jobs.json")
        assert result == expected
        assert os.path.exists(expected)

    def test_urlretrieve_called_with_signed_url(
        self, provider, mock_client, legacy_zip_file, tmp_path
    ):
        """urlretrieve receives the signed URL from the API response."""
        signed_url = "https://storage.googleapis.com/signed/old_jobs.zip"
        dest = str(tmp_path / ".old_jobs.json")
        mock_client.session.get.return_value = _success_response(signed_url)

        with patch("qbraid.runtime.native.provider.urllib.request.urlretrieve") as mock_retrieve:
            mock_retrieve.side_effect = lambda _, dest_zip: shutil.copy(legacy_zip_file, dest_zip)

            with pytest.warns(DeprecationWarning):
                provider.download_legacy_jobs(dest_path=dest)

        mock_retrieve.assert_called_once_with(signed_url, dest + ".zip")


# ---------------------------------------------------------------------------
# download_legacy_jobs — error paths
# ---------------------------------------------------------------------------


class TestDownloadLegacyJobsErrors:
    """Tests for every error branch in download_legacy_jobs."""

    def test_raises_file_exists_error(self, provider, tmp_path):
        """FileExistsError when dest_path already exists on disk."""
        dest = str(tmp_path / ".old_jobs.json")
        with open(dest, "w", encoding="utf-8") as f:
            f.write("{}")

        with pytest.warns(DeprecationWarning):
            with pytest.raises(FileExistsError, match=dest):
                provider.download_legacy_jobs(dest_path=dest)

    def test_raises_on_session_get_value_error(self, provider, mock_client, tmp_path):
        """ValueError from session.get is wrapped in ResourceNotFoundError."""
        mock_client.session.get.side_effect = ValueError("bad response")
        dest = str(tmp_path / ".old_jobs.json")

        with pytest.warns(DeprecationWarning):
            with pytest.raises(ResourceNotFoundError, match="Failed to retrieve"):
                provider.download_legacy_jobs(dest_path=dest)

    def test_raises_on_session_get_quantum_service_error(self, provider, mock_client, tmp_path):
        """QuantumServiceRequestError from session.get is wrapped in ResourceNotFoundError."""
        mock_client.session.get.side_effect = QuantumServiceRequestError("network error")
        dest = str(tmp_path / ".old_jobs.json")

        with pytest.warns(DeprecationWarning):
            with pytest.raises(ResourceNotFoundError, match="Failed to retrieve"):
                provider.download_legacy_jobs(dest_path=dest)

    def test_raises_when_success_is_false(self, provider, mock_client, tmp_path):
        """ResourceNotFoundError when the API returns success=False."""
        resp = MagicMock()
        resp.json.return_value = {"success": False}
        mock_client.session.get.return_value = resp
        dest = str(tmp_path / ".old_jobs.json")

        with pytest.warns(DeprecationWarning):
            with pytest.raises(ResourceNotFoundError, match="Failed to retrieve"):
                provider.download_legacy_jobs(dest_path=dest)

    def test_raises_when_url_missing(self, provider, mock_client, tmp_path):
        """ResourceNotFoundError when 'url' key is absent from data."""
        resp = MagicMock()
        resp.json.return_value = {"success": True, "data": {}}
        mock_client.session.get.return_value = resp
        dest = str(tmp_path / ".old_jobs.json")

        with pytest.warns(DeprecationWarning):
            with pytest.raises(ResourceNotFoundError, match="Download URL not found"):
                provider.download_legacy_jobs(dest_path=dest)

    def test_session_get_called_with_correct_endpoint(self, provider, mock_client, tmp_path):
        """session.get is invoked with the expected /files/download/ endpoint."""
        resp = MagicMock()
        resp.json.return_value = {"success": True, "data": {}}  # will fail at URL check
        mock_client.session.get.return_value = resp
        dest = str(tmp_path / ".old_jobs.json")

        with pytest.warns(DeprecationWarning):
            with pytest.raises(ResourceNotFoundError):
                provider.download_legacy_jobs(dest_path=dest)

        mock_client.session.get.assert_called_once_with("/files/download/.old_jobs.json.zip")

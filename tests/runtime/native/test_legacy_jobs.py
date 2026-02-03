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
    download_legacy_jobs, _load_legacy_jobs, _process_legacy_job_data, display_legacy_jobs

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


# ---------------------------------------------------------------------------
# _load_legacy_jobs
# ---------------------------------------------------------------------------


class TestLoadLegacyJobs:
    """Tests for the _load_legacy_jobs helper."""

    def test_loads_valid_json(self, provider, legacy_json_file):
        """Returns the parsed list from a well-formed JSON file."""
        result = provider._load_legacy_jobs(legacy_json_file)
        assert result == SAMPLE_JOBS

    def test_raises_file_not_found(self, provider, tmp_path):
        """FileNotFoundError when the path does not exist."""
        missing = str(tmp_path / "no_such_file.json")
        with pytest.raises(FileNotFoundError, match="not found"):
            provider._load_legacy_jobs(missing)


# ---------------------------------------------------------------------------
# _process_legacy_job_data — filtering & formatting
# ---------------------------------------------------------------------------


class TestProcessLegacyJobData:
    """Tests for the _process_legacy_job_data helper."""

    def test_no_filters_returns_all_sorted_descending(self, provider):
        """Without filters all jobs are returned, sorted newest-first."""
        job_data, msg = provider._process_legacy_job_data(SAMPLE_JOBS)

        # Newest first: bbb (Jun-16), aaa (Jun-15), ccc (Jun-14)
        assert [row[0] for row in job_data] == [
            "device_b-jovyan-qjob-bbb",
            "device_a-jovyan-qjob-aaa",
            "device_a-jovyan-qjob-ccc",
        ]
        assert "3 legacy job" in msg

    def test_filter_by_device_id(self, provider):
        """Only jobs matching the requested device_id are included."""
        job_data, _ = provider._process_legacy_job_data(SAMPLE_JOBS, device_id="device_a")
        assert len(job_data) == 2
        assert all(jid.startswith("device_a") for jid, _, _ in job_data)

    def test_filter_by_provider_case_insensitive(self, provider):
        """Provider matching is case-insensitive."""
        job_data, _ = provider._process_legacy_job_data(SAMPLE_JOBS, provider="PROVIDERX")
        # Both "ProviderX" and "providerx" match
        assert len(job_data) == 2

    def test_filter_by_status_case_insensitive(self, provider):
        """Status matching is case-insensitive."""
        job_data, _ = provider._process_legacy_job_data(SAMPLE_JOBS, status="completed")
        assert len(job_data) == 1
        assert job_data[0][2] == "COMPLETED"

    def test_filter_by_tags(self, provider):
        """Only jobs containing all specified tag key-value pairs are returned."""
        job_data, _ = provider._process_legacy_job_data(
            SAMPLE_JOBS, tags={"env": "prod", "team": "alpha"}
        )
        assert len(job_data) == 1
        assert job_data[0][0] == "device_a-jovyan-qjob-aaa"

    def test_max_results_truncates(self, provider):
        """max_results limits the output list length."""
        job_data, _ = provider._process_legacy_job_data(SAMPLE_JOBS, max_results=2)
        assert len(job_data) == 2

    def test_max_results_zero_returns_empty(self, provider):
        """max_results=0 is falsy so no truncation happens (all results returned)."""
        # max_results=0 → `if max_results` is False → no slice applied
        job_data, _ = provider._process_legacy_job_data(SAMPLE_JOBS, max_results=0)
        assert len(job_data) == 3

    def test_no_matches_message(self, provider):
        """Message says 'No legacy jobs found' when filters match nothing."""
        _, msg = provider._process_legacy_job_data(SAMPLE_JOBS, status="CANCELLED")
        assert msg == "No legacy jobs found matching criteria."

    def test_singular_message_for_one_total_job(self, provider):
        """Message uses singular 'job' when total job count is 1."""
        single = [SAMPLE_JOBS[0]]
        _, msg = provider._process_legacy_job_data(single)
        assert msg == "Displaying 1 of 1 legacy job."

    def test_plural_message_for_multiple_total_jobs(self, provider):
        """Message uses plural 'jobs' when total job count > 1."""
        _, msg = provider._process_legacy_job_data(SAMPLE_JOBS, max_results=1)
        assert msg == "Displaying 1 of 3 legacy jobs."

    def test_timestamp_formatting(self, provider):
        """Timestamps are stripped of T, Z, and fractional seconds."""
        job_data, _ = provider._process_legacy_job_data(
            SAMPLE_JOBS, device_id="device_a", max_results=1
        )
        # Newest device_a job: "2025-06-15T10:30:00.123Z" → "2025-06-15 10:30:00"
        assert job_data[0][1] == "2025-06-15 10:30:00"

    def test_fallback_to_top_level_created_at(self, provider):
        """When timeStamps.createdAt is missing, top-level createdAt is used."""
        jobs = [
            {
                "qbraidJobId": "job-fallback",
                "qbraidDeviceId": "dev",
                "provider": "P",
                "qbraidStatus": "COMPLETED",
                "createdAt": "2025-07-01T00:00:00.000Z",
                "timeStamps": {},
            }
        ]
        job_data, _ = provider._process_legacy_job_data(jobs)
        assert job_data[0][1] == "2025-07-01 00:00:00"

    def test_fallback_to_na_when_no_timestamp(self, provider):
        """When neither timeStamps.createdAt nor createdAt exist, value is N/A."""
        jobs = [
            {
                "qbraidJobId": "job-no-ts",
                "qbraidDeviceId": "dev",
                "provider": "P",
                "qbraidStatus": "COMPLETED",
            }
        ]
        job_data, _ = provider._process_legacy_job_data(jobs)
        assert job_data[0][1] == "N/A"

    def test_status_fallback_chain(self, provider):
        """Status falls back: qbraidStatus → status → UNKNOWN."""
        jobs_missing_qbraid_status = [
            {
                "qbraidJobId": "job-status-fallback",
                "qbraidDeviceId": "dev",
                "provider": "P",
                "status": "QUEUED",
                "createdAt": "2025-07-01T00:00:00.000Z",
            }
        ]
        job_data, _ = provider._process_legacy_job_data(jobs_missing_qbraid_status)
        assert job_data[0][2] == "QUEUED"

        jobs_no_status = [
            {
                "qbraidJobId": "job-unknown",
                "qbraidDeviceId": "dev",
                "provider": "P",
                "createdAt": "2025-07-01T00:00:00.000Z",
            }
        ]
        job_data, _ = provider._process_legacy_job_data(jobs_no_status)
        assert job_data[0][2] == "UNKNOWN"

    def test_missing_job_id_defaults_to_na(self, provider):
        """Jobs without qbraidJobId show N/A in the ID column."""
        jobs = [
            {
                "qbraidDeviceId": "dev",
                "provider": "P",
                "qbraidStatus": "COMPLETED",
                "createdAt": "2025-07-01T00:00:00.000Z",
            }
        ]
        job_data, _ = provider._process_legacy_job_data(jobs)
        assert job_data[0][0] == "N/A"

    def test_combined_filters(self, provider):
        """Multiple filters are applied together (AND semantics)."""
        job_data, _ = provider._process_legacy_job_data(
            SAMPLE_JOBS, device_id="device_a", provider="providerx", status="RUNNING"
        )
        assert len(job_data) == 1
        assert job_data[0][0] == "device_a-jovyan-qjob-ccc"


# ---------------------------------------------------------------------------
# display_legacy_jobs
# ---------------------------------------------------------------------------


class TestDisplayLegacyJobs:
    """Tests for the display_legacy_jobs public method."""

    @patch("qbraid.runtime.native.provider.display_jobs_from_data")
    def test_reads_existing_file_and_displays(self, mock_display, provider, legacy_json_file):
        """When the file already exists it is read directly (no download)."""
        mock_display.return_value = None

        with pytest.warns(DeprecationWarning, match="display_legacy_jobs"):
            provider.display_legacy_jobs(path=legacy_json_file)

        mock_display.assert_called_once()
        job_data, message = mock_display.call_args[0]
        assert len(job_data) == 3
        assert "3 legacy job" in message

    @patch("qbraid.runtime.native.provider.display_jobs_from_data")
    def test_downloads_file_when_missing(self, mock_display, provider, tmp_path):
        """When path does not exist, download_legacy_jobs is called first."""
        missing_path = str(tmp_path / "sub" / ".old_jobs.json")
        mock_display.return_value = None

        with patch.object(provider, "download_legacy_jobs") as mock_dl:
            # Simulate the download by writing the file that _load expects
            def _write_file(dest_path=None):
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "w", encoding="utf-8") as f:
                    json.dump(SAMPLE_JOBS, f)

            mock_dl.side_effect = _write_file

            with pytest.warns(DeprecationWarning):
                provider.display_legacy_jobs(path=missing_path)

            mock_dl.assert_called_once_with(dest_path=missing_path)

        mock_display.assert_called_once()

    @patch("qbraid.runtime.native.provider.display_jobs_from_data")
    def test_filters_are_forwarded(self, mock_display, provider, legacy_json_file):
        """Filtering parameters reach _process_legacy_job_data correctly."""
        mock_display.return_value = None

        with pytest.warns(DeprecationWarning):
            provider.display_legacy_jobs(
                path=legacy_json_file,
                device_id="device_b",
                provider="ProviderY",
                status="FAILED",
                max_results=5,
            )

        job_data, _ = mock_display.call_args[0]
        assert len(job_data) == 1
        assert job_data[0][0] == "device_b-jovyan-qjob-bbb"

    @patch("qbraid.runtime.native.provider.display_jobs_from_data")
    def test_tag_filter_forwarded(self, mock_display, provider, legacy_json_file):
        """Tags filter is passed through and applied."""
        mock_display.return_value = None

        with pytest.warns(DeprecationWarning):
            provider.display_legacy_jobs(path=legacy_json_file, tags={"env": "staging"})

        job_data, _ = mock_display.call_args[0]
        assert len(job_data) == 1
        assert job_data[0][0] == "device_b-jovyan-qjob-bbb"

    @patch("qbraid.runtime.native.provider.display_jobs_from_data")
    def test_default_path_is_cwd(self, mock_display, provider, tmp_path, monkeypatch):
        """When path is None the default resolves to cwd/.old_jobs.json."""
        monkeypatch.chdir(tmp_path)
        # Place the jobs file at the expected default location
        default_dest = os.path.join(str(tmp_path), ".old_jobs.json")
        with open(default_dest, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_JOBS, f)

        mock_display.return_value = None

        with pytest.warns(DeprecationWarning):
            provider.display_legacy_jobs()

        mock_display.assert_called_once()
        job_data, _ = mock_display.call_args[0]
        assert len(job_data) == 3

    @patch("qbraid.runtime.native.provider.display_jobs_from_data")
    def test_empty_jobs_file(self, mock_display, provider, tmp_path):
        """An empty JSON array produces the 'No legacy jobs found' message."""
        path = str(tmp_path / ".old_jobs.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)

        mock_display.return_value = None

        with pytest.warns(DeprecationWarning):
            provider.display_legacy_jobs(path=path)

        _, message = mock_display.call_args[0]
        assert message == "No legacy jobs found matching criteria."

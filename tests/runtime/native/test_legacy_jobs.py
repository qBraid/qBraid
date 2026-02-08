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
Unit tests for QbraidProvider legacy jobs functionality.

"""
import json
from unittest.mock import MagicMock, patch

import pytest

from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.native import QbraidProvider


@pytest.fixture
def legacy_jobs_file(tmp_path):
    """Create a temporary legacy jobs JSON file for testing."""
    jobs_data = [
        {
            "qbraidJobId": "job-001",
            "vendorJobId": "vendor-001",
            "_id": "507f1f77bcf86cd799439011",
            "vendor": "aws",
            "provider": "aws",
            "status": "COMPLETED",
            "qbraidDeviceId": "aws_sv1",
            "shots": 100,
            "measurementCounts": {"00": 50, "11": 50},
            "measurements": [[0, 0], [1, 1]],
        },
        {
            "qbraidJobId": "job-002",
            "vendorJobId": "vendor-002",
            "_id": "507f1f77bcf86cd799439012",
            "vendor": "ibm",
            "provider": "ibm",
            "status": "FAILED",
            "qbraidDeviceId": "ibm_kyiv",
            "shots": 50,
            "measurementCounts": {},
            "measurements": [],
        },
        {
            "qbraidJobId": "job-003",
            "vendorJobId": "vendor-003",
            "_id": "507f1f77bcf86cd799439013",
            "vendor": "aws",
            "provider": "aws",
            "status": "COMPLETED",
            "qbraidDeviceId": "aws_tn1",
            "shots": 200,
            "measurementCounts": {"000": 100, "111": 100},
            "measurements": [],
        },
    ]

    file_path = tmp_path / "legacy_jobs.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(jobs_data, f)

    return str(file_path)


class TestLegacyJobsProviderInit:
    """Tests for QbraidProvider initialization with legacy jobs."""

    def test_provider_init_with_legacy_jobs_path(self, legacy_jobs_file):
        """Test QbraidProvider can be initialized with legacy_jobs_path."""
        provider = QbraidProvider(legacy_jobs_path=legacy_jobs_file)
        assert provider._legacy_jobs_path == legacy_jobs_file

    def test_provider_init_with_api_key_and_client_raises(self):
        """Test that providing both api_key and client raises ValueError."""
        mock_client = MagicMock()
        with pytest.raises(ValueError, match="Provide either api_key or client, not both"):
            QbraidProvider(api_key="test_key", client=mock_client)

    def test_provider_client_property_with_legacy_path(self, legacy_jobs_file):
        """Test that client is created with legacy_jobs_path."""
        with patch("qbraid.runtime.native.provider.QuantumClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            provider = QbraidProvider(legacy_jobs_path=legacy_jobs_file)
            _ = provider.client

            mock_client_class.assert_called_once_with(
                api_key=None, legacy_jobs_path=legacy_jobs_file
            )


class TestLegacyJobsDeviceRestrictions:
    """Tests for device operations when using legacy jobs."""

    def test_get_devices_raises_with_legacy_jobs(self, legacy_jobs_file):
        """Test get_devices raises ResourceNotFoundError with legacy jobs."""
        provider = QbraidProvider(legacy_jobs_path=legacy_jobs_file)

        with pytest.raises(
            ResourceNotFoundError,
            match="Device information is not available when using a legacy jobs file",
        ):
            provider.get_devices()

    def test_get_device_raises_with_legacy_jobs(self, legacy_jobs_file):
        """Test get_device raises ResourceNotFoundError with legacy jobs."""
        provider = QbraidProvider(legacy_jobs_path=legacy_jobs_file)

        with pytest.raises(
            ResourceNotFoundError,
            match="Device information is not available when using a legacy jobs file",
        ):
            provider.get_device("some_device_id")


class TestLegacyJobsDisplayJobs:
    """Tests for display_jobs functionality with legacy jobs."""

    def test_display_jobs_with_legacy_file(self, legacy_jobs_file):
        """Test display_jobs works with legacy jobs file by calling client.search_jobs."""
        with patch("qbraid.runtime.native.provider.QuantumClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search_jobs.return_value = [
                {
                    "qbraidJobId": "job-001",
                    "status": "COMPLETED",
                    "qbraidDeviceId": "aws_sv1",
                }
            ]
            mock_client_class.return_value = mock_client

            with patch("qbraid.runtime.native.provider.process_job_data") as mock_process:
                mock_process.return_value = ([], None)

                with patch("qbraid.runtime.native.provider.display_jobs_from_data") as mock_display:
                    provider = QbraidProvider(legacy_jobs_path=legacy_jobs_file)
                    provider.display_jobs(max_results=5)

                    mock_client.search_jobs.assert_called_once()
                    mock_process.assert_called_once()
                    mock_display.assert_called_once()

    def test_display_jobs_filters_passed_to_client(self, legacy_jobs_file):
        """Test that filters are correctly passed to client.search_jobs."""
        with patch("qbraid.runtime.native.provider.QuantumClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search_jobs.return_value = []
            mock_client_class.return_value = mock_client

            with patch("qbraid.runtime.native.provider.process_job_data") as mock_process:
                mock_process.return_value = ([], None)

                with patch("qbraid.runtime.native.provider.display_jobs_from_data"):
                    provider = QbraidProvider(legacy_jobs_path=legacy_jobs_file)
                    provider.display_jobs(
                        device_id="aws_sv1",
                        provider="aws",
                        status="COMPLETED",
                        tags={"tag1": "value1"},
                        max_results=3,
                    )

                    expected_query = {
                        "provider": "aws",
                        "qbraidDeviceId": "aws_sv1",
                        "status": "COMPLETED",
                        "tags.tag1": "value1",
                        "resultsPerPage": 3,
                    }
                    mock_client.search_jobs.assert_called_once_with(expected_query)


class TestLegacyJobsHash:
    """Tests for provider hashing with legacy jobs."""

    def test_hash_with_legacy_jobs_uses_file_path(self, legacy_jobs_file):
        """Test that hash is computed based on file path for legacy jobs."""
        provider = QbraidProvider(legacy_jobs_path=legacy_jobs_file)
        hash1 = hash(provider)

        # Same file path should produce same hash
        provider2 = QbraidProvider(legacy_jobs_path=legacy_jobs_file)
        hash2 = hash(provider2)

        assert hash1 == hash2

    def test_hash_different_for_different_legacy_paths(self, tmp_path):
        """Test that different file paths produce different hashes."""
        # Create two different legacy job files
        file1 = tmp_path / "jobs1.json"
        file2 = tmp_path / "jobs2.json"

        with open(file1, "w", encoding="utf-8") as f:
            json.dump([], f)
        with open(file2, "w", encoding="utf-8") as f:
            json.dump([], f)

        provider1 = QbraidProvider(legacy_jobs_path=str(file1))
        provider2 = QbraidProvider(legacy_jobs_path=str(file2))

        assert hash(provider1) != hash(provider2)

    def test_hash_is_cached(self, legacy_jobs_file):
        """Test that hash is computed only once and cached."""
        provider = QbraidProvider(legacy_jobs_path=legacy_jobs_file)

        # Access hash twice
        hash1 = hash(provider)
        hash2 = hash(provider)

        assert hash1 == hash2
        assert hasattr(provider, "_hash")


class TestLegacyJobsFileNotFound:
    """Tests for error handling when legacy jobs file doesn't exist."""

    def test_search_jobs_raises_when_legacy_file_not_found(self):
        """Test that search_jobs raises when legacy file doesn't exist."""
        provider = QbraidProvider(legacy_jobs_path="/nonexistent/path/jobs.json")

        # The FileNotFoundError is raised when actually loading/searching jobs,
        # not at client instantiation
        with pytest.raises(FileNotFoundError):
            provider.client.search_jobs()

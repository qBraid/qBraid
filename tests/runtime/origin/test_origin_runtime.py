# Copyright (C) 2026 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for OriginQ provider, device, and job classes.

"""
from unittest.mock import MagicMock, patch

import pytest

from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.origin import OriginDevice, OriginJob, OriginProvider
from qbraid.runtime.origin.job import _map_status, _normalize_status, OriginJobError
from qbraid.runtime.origin.provider import _resolve_api_key


# --- API key resolution ---


class TestResolveApiKey:
    def test_explicit_key(self):
        assert _resolve_api_key("my-key") == "my-key"

    def test_env_variable(self, monkeypatch):
        monkeypatch.setenv("ORIGIN_API_KEY", "env-key")
        assert _resolve_api_key() == "env-key"

    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("ORIGIN_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OriginQ API key is required"):
            _resolve_api_key()


# --- Status mapping ---


class TestStatusMapping:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("FINISH", JobStatus.COMPLETED),
            ("FINISHED", JobStatus.COMPLETED),
            ("COMPLETED", JobStatus.COMPLETED),
            ("WAITING", JobStatus.QUEUED),
            ("QUEUING", JobStatus.QUEUED),
            ("COMPUTING", JobStatus.RUNNING),
            ("RUNNING", JobStatus.RUNNING),
            ("FAILED", JobStatus.FAILED),
            ("ERROR", JobStatus.FAILED),
            ("SOMETHING_ELSE", JobStatus.UNKNOWN),
        ],
    )
    def test_map_status_strings(self, raw, expected):
        assert _map_status(raw) == expected

    def test_normalize_enum_with_name(self):
        mock_enum = MagicMock()
        mock_enum.name = "FINISHED"
        assert _normalize_status(mock_enum) == "FINISHED"

    def test_normalize_strips_prefix(self):
        assert _normalize_status("JOBSTATUS.COMPLETED") == "COMPLETED"
        assert _normalize_status("JOB_RUNNING") == "RUNNING"


# --- Provider ---


class TestOriginProvider:
    @patch("qbraid.runtime.origin.provider._get_service")
    def test_get_device(self, mock_get_service, monkeypatch):
        monkeypatch.setenv("ORIGIN_API_KEY", "test-key")

        mock_service = MagicMock()
        mock_backend = MagicMock()
        mock_backend.chip_info.side_effect = Exception("no chip info")
        mock_service.backend.return_value = mock_backend
        mock_get_service.return_value = mock_service

        with patch("qbraid.runtime.origin.provider.ProgramSpec"):
            provider = OriginProvider(api_key="test-key")
            device = provider.get_device("full_amplitude")

        assert isinstance(device, OriginDevice)
        assert device.id == "full_amplitude"

    @patch("qbraid.runtime.origin.provider._get_service")
    def test_get_devices_filters_unavailable(self, mock_get_service, monkeypatch):
        monkeypatch.setenv("ORIGIN_API_KEY", "test-key")

        mock_service = MagicMock()
        mock_service.backends.return_value = {
            "full_amplitude": True,
            "offline_device": False,
        }
        mock_backend = MagicMock()
        mock_backend.chip_info.side_effect = Exception("no chip info")
        mock_service.backend.return_value = mock_backend
        mock_get_service.return_value = mock_service

        with patch("qbraid.runtime.origin.provider.ProgramSpec"):
            provider = OriginProvider(api_key="test-key")
            devices = provider.get_devices()

        assert len(devices) == 1
        assert devices[0].id == "full_amplitude"


# --- Device ---


class TestOriginDevice:
    def _make_device(self, backend_name="full_amplitude", device_id=None):
        device_id = device_id or backend_name
        mock_backend = MagicMock()
        mock_service = MagicMock()
        profile = MagicMock()
        profile.device_id = device_id
        profile.simulator = backend_name in {"full_amplitude", "partial_amplitude", "single_amplitude"}
        profile.num_qubits = 35 if profile.simulator else None
        return OriginDevice(
            profile=profile,
            backend=mock_backend,
            backend_name=backend_name,
            service=mock_service,
        )

    def test_status_always_online(self):
        device = self._make_device()
        assert device.status() == DeviceStatus.ONLINE


# --- Job ---


class TestOriginJob:
    def test_status_completed(self):
        mock_backend_job = MagicMock()
        mock_backend_job.status.return_value = "FINISHED"

        job = OriginJob(job_id="test-123", backend_job=mock_backend_job)
        assert job.status() == JobStatus.COMPLETED

    def test_status_unknown_on_error(self):
        mock_backend_job = MagicMock()
        mock_backend_job.status.side_effect = Exception("connection error")

        job = OriginJob(job_id="test-123", backend_job=mock_backend_job)
        assert job.status() == JobStatus.UNKNOWN

    def test_cancel_raises(self):
        job = OriginJob(job_id="test-123")
        with pytest.raises(OriginJobError, match="does not support"):
            job.cancel()

    def test_result_returns_counts(self):
        mock_result = MagicMock()
        mock_result.get_counts.return_value = {"00": 500, "11": 500}

        mock_backend_job = MagicMock()
        mock_backend_job.result.return_value = mock_result
        mock_backend_job.status.return_value = "FINISHED"

        mock_device = MagicMock()
        mock_device.profile.device_id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, backend_job=mock_backend_job)
        result = job.result()

        assert result.success is True
        assert result.data.measurement_counts == {"00": 500, "11": 500}

    def test_result_fallback_to_counts_list(self):
        mock_result = MagicMock()
        mock_result.get_counts.return_value = {}
        mock_result.get_counts_list.return_value = [{"00": 400, "11": 600}]

        mock_backend_job = MagicMock()
        mock_backend_job.result.return_value = mock_result
        mock_backend_job.status.return_value = "FINISHED"

        mock_device = MagicMock()
        mock_device.profile.device_id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, backend_job=mock_backend_job)
        result = job.result()

        assert result.data.measurement_counts == {"00": 400, "11": 600}

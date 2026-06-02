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
# pylint: disable=too-many-public-methods,too-many-arguments

"""
Unit tests for OriginQ provider, device, and job classes.

"""
import json
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("pyqpanda3", reason="pyqpanda3 is not installed.")

# pylint: disable=wrong-import-position
from qbraid.runtime.enums import DeviceStatus, JobStatus  # noqa: E402
from qbraid.runtime.origin import OriginDevice, OriginJob, OriginProvider  # noqa: E402
from qbraid.runtime.origin.device import OriginDeviceError  # noqa: E402
from qbraid.runtime.origin.job import (  # noqa: E402
    _ORIGIN_STATUS_MAP,
    OriginJobError,
    _map_origin_status,
)
from qbraid.runtime.origin.provider import (  # noqa: E402
    _get_service,
    _infer_basis_gates,
    _resolve_api_key,
)
from qbraid.runtime.result import Result  # noqa: E402
from qbraid.runtime.result_data import GateModelResultData  # noqa: E402

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
    def test_map_finished(self):
        mock_status = MagicMock()
        mock_status.name = "FINISHED"
        assert _map_origin_status(mock_status) == JobStatus.COMPLETED

    def test_map_waiting(self):
        mock_status = MagicMock()
        mock_status.name = "WAITING"
        assert _map_origin_status(mock_status) == JobStatus.QUEUED

    def test_map_queuing(self):
        mock_status = MagicMock()
        mock_status.name = "QUEUING"
        assert _map_origin_status(mock_status) == JobStatus.QUEUED

    def test_map_computing(self):
        mock_status = MagicMock()
        mock_status.name = "COMPUTING"
        assert _map_origin_status(mock_status) == JobStatus.RUNNING

    def test_map_failed(self):
        mock_status = MagicMock()
        mock_status.name = "FAILED"
        assert _map_origin_status(mock_status) == JobStatus.FAILED

    def test_map_unknown_raises(self):
        mock_status = MagicMock()
        mock_status.name = "SOMETHING_ELSE"
        with pytest.raises(ValueError, match="Unknown OriginQ job status"):
            _map_origin_status(mock_status)

    def test_all_expected_statuses_covered(self):
        expected = {"FINISHED", "WAITING", "QUEUING", "COMPUTING", "FAILED"}
        assert set(_ORIGIN_STATUS_MAP.keys()) == expected


# --- Provider ---


class TestOriginProvider:
    @patch("qbraid.runtime.origin.provider._get_service")
    def test_get_device(self, mock_get_service, monkeypatch):
        monkeypatch.setenv("ORIGIN_API_KEY", "test-key")

        mock_service = MagicMock()
        mock_backend = MagicMock()
        mock_backend.name.return_value = "full_amplitude"
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
        mock_backend.name.return_value = "full_amplitude"
        mock_backend.chip_info.side_effect = Exception("no chip info")
        mock_service.backend.return_value = mock_backend
        mock_get_service.return_value = mock_service

        with patch("qbraid.runtime.origin.provider.ProgramSpec"):
            provider = OriginProvider(api_key="test-key")
            devices = provider.get_devices()

        assert len(devices) == 1
        assert devices[0].id == "full_amplitude"

    @patch("qbraid.runtime.origin.provider._get_service")
    def test_get_devices_hardware_only(self, mock_get_service, monkeypatch):
        monkeypatch.setenv("ORIGIN_API_KEY", "test-key")

        mock_service = MagicMock()
        mock_service.backends.return_value = {
            "full_amplitude": True,
            "WK_C180": True,
        }
        mock_backend = MagicMock()
        mock_backend.name.return_value = "WK_C180"
        chip_info = MagicMock()
        chip_info.qubits_num.return_value = 180
        chip_info.get_basic_gates.return_value = ["H", "CNOT"]
        mock_backend.chip_info.return_value = chip_info
        mock_service.backend.return_value = mock_backend
        mock_get_service.return_value = mock_service

        with patch("qbraid.runtime.origin.provider.ProgramSpec"):
            provider = OriginProvider(api_key="test-key")
            devices = provider.get_devices(hardware_only=True)

        assert len(devices) == 1
        assert devices[0].id == "WK_C180"

    def test_provider_hash_is_stable(self, monkeypatch):
        monkeypatch.setenv("ORIGIN_API_KEY", "test-key")
        provider = OriginProvider(api_key="test-key")
        assert hash(provider) == hash(provider)


# --- Device ---


def _make_device(
    backend_name="full_amplitude",
    backend=None,
    service=None,
):
    """Helper to create an OriginDevice with mocked dependencies."""
    mock_backend = backend or MagicMock()
    mock_service = service or MagicMock()
    profile = MagicMock()
    profile.device_id = backend_name
    profile.simulator = backend_name in {
        "full_amplitude",
        "partial_amplitude",
        "single_amplitude",
    }
    return OriginDevice(
        profile=profile,
        backend=mock_backend,
        service=mock_service,
    )


class TestOriginDevice:
    def test_str_representation(self):
        device = _make_device()
        assert "OriginDevice" in str(device)
        assert "full_amplitude" in str(device)

    def test_status_online(self):
        mock_service = MagicMock()
        mock_service.backends.return_value = {"full_amplitude": True}
        device = _make_device(service=mock_service)
        assert device.status() == DeviceStatus.ONLINE

    def test_status_offline(self):
        mock_service = MagicMock()
        mock_service.backends.return_value = {"full_amplitude": False}
        device = _make_device(service=mock_service)
        assert device.status() == DeviceStatus.OFFLINE

    def test_status_not_found_raises(self):
        mock_service = MagicMock()
        mock_service.backends.return_value = {"other_device": True}
        device = _make_device(service=mock_service)
        with pytest.raises(OriginDeviceError, match="not found"):
            device.status()

    def test_backend_lazy_init(self):
        mock_service = MagicMock()
        mock_lazy_backend = MagicMock()
        mock_service.backend.return_value = mock_lazy_backend

        profile = MagicMock()
        profile.device_id = "full_amplitude"
        profile.simulator = True

        device = OriginDevice(profile=profile, backend=None, service=mock_service)
        assert device.backend is mock_lazy_backend
        mock_service.backend.assert_called_once_with("full_amplitude")

    def test_submit_simulator(self):
        mock_backend = MagicMock()
        mock_qcloud_job = MagicMock()
        mock_qcloud_job.job_id.return_value = "test-job-123"
        mock_backend.run.return_value = mock_qcloud_job

        device = _make_device(backend=mock_backend)
        mock_prog = MagicMock()
        job = device.submit(mock_prog, shots=100)

        mock_backend.run.assert_called_once_with(mock_prog, 100)
        assert isinstance(job, OriginJob)
        assert job.id == "test-job-123"

    @patch("pyqpanda3.qcloud.QCloudOptions")
    def test_submit_hardware(self, mock_options_cls):
        mock_backend = MagicMock()
        mock_qcloud_job = MagicMock()
        mock_qcloud_job.job_id.return_value = "hw-job-456"
        mock_backend.run.return_value = mock_qcloud_job

        profile = MagicMock()
        profile.device_id = "WK_C180"
        profile.simulator = False
        mock_service = MagicMock()
        device = OriginDevice(profile=profile, backend=mock_backend, service=mock_service)
        mock_prog = MagicMock()
        job = device.submit(mock_prog, shots=1000)

        mock_backend.run.assert_called_once_with(mock_prog, 1000, mock_options_cls.return_value)
        assert job.id == "hw-job-456"

    def test_submit_batch_simulator_returns_list(self):
        mock_backend = MagicMock()
        mock_job_1 = MagicMock()
        mock_job_1.job_id.return_value = "job-1"
        mock_job_2 = MagicMock()
        mock_job_2.job_id.return_value = "job-2"
        mock_backend.run.side_effect = [mock_job_1, mock_job_2]

        device = _make_device(backend=mock_backend)
        progs = [MagicMock(), MagicMock()]
        jobs = device.submit(progs, shots=100)

        assert isinstance(jobs, list)
        assert len(jobs) == 2
        assert jobs[0].id == "job-1"
        assert jobs[1].id == "job-2"
        assert mock_backend.run.call_count == 2

    @patch("pyqpanda3.qcloud.QCloudOptions")
    def test_submit_batch_hardware(self, mock_options_cls):
        mock_backend = MagicMock()
        mock_qcloud_job = MagicMock()
        mock_qcloud_job.job_id.return_value = "batch-job-789"
        mock_backend.run.return_value = mock_qcloud_job

        profile = MagicMock()
        profile.device_id = "WK_C180"
        profile.simulator = False
        mock_service = MagicMock()
        device = OriginDevice(profile=profile, backend=mock_backend, service=mock_service)
        progs = [MagicMock(), MagicMock()]
        job = device.submit(progs, shots=100)

        mock_backend.run.assert_called_once_with(progs, 100, mock_options_cls.return_value)
        assert isinstance(job, OriginJob)
        assert job.id == "batch-job-789"


# --- Job ---


def _make_mock_qcloud_job(
    job_id="test-123",
    status_name="FINISHED",
    origin_data=None,
    counts_list=None,
    probs_list=None,
    counts_list_error=False,
    probs_list_error=False,
):
    """Helper to create a mock QCloudJob with configurable result behavior."""
    mock_status = MagicMock()
    mock_status.name = status_name

    mock_result = MagicMock()

    if origin_data is None:
        origin_data = json.dumps(
            {
                "success": True,
                "code": 10000,
                "message": "success",
                "obj": {"taskId": job_id, "totalTime": 1234},
            }
        )
    mock_result.origin_data.return_value = origin_data

    if counts_list_error:
        mock_result.get_counts_list.side_effect = RuntimeError("convert error")
    else:
        mock_result.get_counts_list.return_value = counts_list or []

    if probs_list_error:
        mock_result.get_probs_list.side_effect = RuntimeError("convert error")
    else:
        mock_result.get_probs_list.return_value = probs_list or []

    mock_job = MagicMock()
    mock_job.job_id.return_value = job_id
    mock_job.status.return_value = mock_status
    mock_job.result.return_value = mock_result

    return mock_job


class TestOriginJob:
    def test_create_with_job_object(self):
        mock_job = MagicMock()
        mock_job.job_id.return_value = "abc-123"

        job = OriginJob(job_id="abc-123", job=mock_job)
        assert job.id == "abc-123"

    def test_create_with_mismatched_job_id_raises(self):
        mock_job = MagicMock()
        mock_job.job_id.return_value = "different-id"

        with pytest.raises(OriginJobError, match="does not match"):
            OriginJob(job_id="abc-123", job=mock_job)

    @patch("qbraid.runtime.origin.job.OriginJob._get_job")
    def test_create_with_device_and_service(self, mock_get_job):
        mock_qcloud_job = MagicMock()
        mock_get_job.return_value = mock_qcloud_job

        mock_device = MagicMock()
        mock_device.id = "full_amplitude"
        mock_service = MagicMock()

        job = OriginJob(job_id="abc-123", device=mock_device, service=mock_service)
        assert job.id == "abc-123"
        assert job._device is mock_device

    def test_create_from_job_id_only(self):
        """Reconstruct job from just an ID (requires pyqpanda3 runtime import)."""
        with patch("qbraid.runtime.origin.job.OriginJob._get_job") as mock_get_job:
            mock_qcloud_job = MagicMock()
            mock_get_job.return_value = mock_qcloud_job

            job = OriginJob(job_id="abc-123")
            assert job.id == "abc-123"
            assert job._device is None

    def test_status_completed(self):
        mock_job = _make_mock_qcloud_job(status_name="FINISHED")
        job = OriginJob(job_id="test-123", job=mock_job)
        assert job.status() == JobStatus.COMPLETED

    def test_status_queued(self):
        mock_job = _make_mock_qcloud_job(status_name="WAITING")
        job = OriginJob(job_id="test-123", job=mock_job)
        assert job.status() == JobStatus.QUEUED

    def test_status_running(self):
        mock_job = _make_mock_qcloud_job(status_name="COMPUTING")
        job = OriginJob(job_id="test-123", job=mock_job)
        assert job.status() == JobStatus.RUNNING

    def test_status_failed(self):
        mock_job = _make_mock_qcloud_job(status_name="FAILED")
        job = OriginJob(job_id="test-123", job=mock_job)
        assert job.status() == JobStatus.FAILED

    def test_status_caches_in_metadata(self):
        mock_job = _make_mock_qcloud_job(status_name="FINISHED")
        job = OriginJob(job_id="test-123", job=mock_job)
        job.status()
        assert job._cache_metadata["status"] == JobStatus.COMPLETED

    def test_status_error_raises(self):
        mock_job = MagicMock()
        mock_job.job_id.return_value = "test-123"
        mock_job.status.side_effect = RuntimeError("connection error")

        job = OriginJob(job_id="test-123", job=mock_job)
        with pytest.raises(OriginJobError, match="Unable to retrieve job status"):
            job.status()

    def test_status_cluster_failure_maps_to_failed(self):
        """pyqpanda3 raises RuntimeError for cluster-level failures; map to FAILED."""
        mock_job = MagicMock()
        mock_job.job_id.return_value = "test-123"
        mock_job.status.side_effect = RuntimeError(
            "query qcloud task failed: Error: the task was failed on cluster: 202"
        )

        job = OriginJob(job_id="test-123", job=mock_job)
        assert job.status() == JobStatus.FAILED
        # Subsequent calls should return the cached terminal status
        assert job.status() == JobStatus.FAILED

    def test_cancel_raises(self):
        mock_job = MagicMock()
        mock_job.job_id.return_value = "test-123"
        job = OriginJob(job_id="test-123", job=mock_job)
        with pytest.raises(OriginJobError, match="does not support"):
            job.cancel()

    def test_result_with_probabilities(self):
        mock_job = _make_mock_qcloud_job(
            probs_list=[{"00": 0.5, "11": 0.5}],
            counts_list_error=True,
        )

        mock_device = MagicMock()
        mock_device.id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, job=mock_job)
        result = job.result()

        assert isinstance(result, Result)
        assert result.success is True
        assert result.device_id == "full_amplitude"
        assert result.job_id == "test-123"
        assert isinstance(result.data, GateModelResultData)
        assert result.data.measurement_counts is None
        assert result.data._measurement_probabilities == {"00": 0.5, "11": 0.5}

    def test_result_with_counts(self):
        mock_job = _make_mock_qcloud_job(
            counts_list=[{"00": 500, "11": 500}],
            probs_list_error=True,
        )

        mock_device = MagicMock()
        mock_device.id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, job=mock_job)
        result = job.result()

        assert result.data.measurement_counts == {"00": 500, "11": 500}

    def test_result_batch_probabilities(self):
        mock_job = _make_mock_qcloud_job(
            probs_list=[
                {"00": 0.5, "11": 0.5},
                {"00": 0.3, "01": 0.7},
            ],
            counts_list_error=True,
        )

        mock_device = MagicMock()
        mock_device.id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, job=mock_job)
        result = job.result()

        probs = result.data._measurement_probabilities
        assert isinstance(probs, list)
        assert len(probs) == 2
        assert probs[0] == {"00": 0.5, "11": 0.5}
        assert probs[1] == {"00": 0.3, "01": 0.7}

    def test_result_batch_counts(self):
        mock_job = _make_mock_qcloud_job(
            counts_list=[
                {"00": 500, "11": 500},
                {"00": 300, "01": 700},
            ],
            probs_list_error=True,
        )

        mock_device = MagicMock()
        mock_device.id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, job=mock_job)
        result = job.result()

        counts = result.data.measurement_counts
        assert isinstance(counts, list)
        assert len(counts) == 2
        assert counts[0] == {"00": 500, "11": 500}
        assert counts[1] == {"00": 300, "01": 700}

    def test_result_no_device_uses_fallback_id(self):
        mock_job = _make_mock_qcloud_job(
            probs_list=[{"00": 0.5, "11": 0.5}],
            counts_list_error=True,
        )

        job = OriginJob(job_id="test-123", job=mock_job)
        result = job.result()

        assert result.device_id == "origin"

    def test_result_fetch_error_raises(self):
        mock_job = MagicMock()
        mock_job.job_id.return_value = "test-123"

        mock_status = MagicMock()
        mock_status.name = "FINISHED"
        mock_job.status.return_value = mock_status
        mock_job.result.side_effect = RuntimeError("API error")

        job = OriginJob(job_id="test-123", job=mock_job)
        with pytest.raises(OriginJobError, match="Failed to fetch results"):
            job.result()

    def test_result_cluster_failure_raises(self):
        """A job that failed on the cluster should raise a clean error from result()."""
        mock_job = MagicMock()
        mock_job.job_id.return_value = "test-123"
        mock_job.status.side_effect = RuntimeError(
            "query qcloud task failed: Error: the task was failed on cluster: 202"
        )

        job = OriginJob(job_id="test-123", job=mock_job)
        with pytest.raises(OriginJobError, match="failed on the cluster"):
            job.result()

    def test_result_no_counts_no_probs(self):
        mock_job = _make_mock_qcloud_job(
            counts_list_error=True,
            probs_list_error=True,
        )
        mock_device = MagicMock()
        mock_device.id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, job=mock_job)
        result = job.result()

        assert result.data.measurement_counts is None
        assert result.data._measurement_probabilities is None

    def test_result_success_from_origin_data(self):
        mock_job = _make_mock_qcloud_job(
            origin_data=json.dumps({"success": False, "obj": {}}),
            counts_list_error=True,
            probs_list_error=True,
        )
        mock_device = MagicMock()
        mock_device.id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, job=mock_job)
        result = job.result()

        assert result.success is False

    def test_result_missing_success_falls_back_to_status(self):
        mock_job = _make_mock_qcloud_job(
            origin_data=json.dumps({"obj": {}}),
            counts_list_error=True,
            probs_list_error=True,
        )
        mock_device = MagicMock()
        mock_device.id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, job=mock_job)
        result = job.result()

        assert result.success is True

    def test_result_malformed_origin_data_raises(self):
        mock_job = _make_mock_qcloud_job(
            origin_data="not valid json",
            probs_list=[{"00": 1.0}],
            counts_list_error=True,
        )
        mock_device = MagicMock()
        mock_device.id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, job=mock_job)
        with pytest.raises(json.JSONDecodeError):
            job.result()

    def test_result_metadata_passed_through(self):
        mock_job = _make_mock_qcloud_job(
            origin_data=json.dumps(
                {
                    "success": True,
                    "obj": {
                        "taskId": "test-123",
                        "totalTime": 5000,
                        "queueTime": 100,
                    },
                }
            ),
            probs_list=[{"00": 1.0}],
            counts_list_error=True,
        )
        mock_device = MagicMock()
        mock_device.id = "full_amplitude"

        job = OriginJob(job_id="test-123", device=mock_device, job=mock_job)
        result = job.result()

        obj = result._details["obj"]
        assert obj["totalTime"] == 5000
        assert obj["queueTime"] == 100

    def test_repr(self):
        mock_job = MagicMock()
        mock_job.job_id.return_value = "test-123"
        job = OriginJob(job_id="test-123", job=mock_job)
        assert "test-123" in repr(job)
        assert "OriginJob" in repr(job)


# --- Extract results ---


class TestExtractResults:
    def test_single_probs(self):
        mock_result = MagicMock()
        mock_result.get_counts_list.side_effect = RuntimeError
        mock_result.get_probs_list.return_value = [{"00": 0.5, "11": 0.5}]

        counts, probs = OriginJob._extract_results(mock_result)
        assert counts is None
        assert probs == {"00": 0.5, "11": 0.5}

    def test_batch_probs(self):
        mock_result = MagicMock()
        mock_result.get_counts_list.side_effect = RuntimeError
        mock_result.get_probs_list.return_value = [
            {"00": 0.5, "11": 0.5},
            {"01": 1.0},
        ]

        counts, probs = OriginJob._extract_results(mock_result)
        assert counts is None
        assert isinstance(probs, list)
        assert len(probs) == 2

    def test_single_counts(self):
        mock_result = MagicMock()
        mock_result.get_counts_list.return_value = [{"00": 500, "11": 500}]
        mock_result.get_probs_list.side_effect = RuntimeError

        counts, probs = OriginJob._extract_results(mock_result)
        assert counts == {"00": 500, "11": 500}
        assert probs is None

    def test_both_counts_and_probs(self):
        mock_result = MagicMock()
        mock_result.get_counts_list.return_value = [{"00": 500, "11": 500}]
        mock_result.get_probs_list.return_value = [{"00": 0.5, "11": 0.5}]

        counts, probs = OriginJob._extract_results(mock_result)
        assert counts == {"00": 500, "11": 500}
        assert probs == {"00": 0.5, "11": 0.5}

    def test_neither_counts_nor_probs(self):
        mock_result = MagicMock()
        mock_result.get_counts_list.side_effect = RuntimeError
        mock_result.get_probs_list.side_effect = RuntimeError

        counts, probs = OriginJob._extract_results(mock_result)
        assert counts is None
        assert probs is None

    def test_empty_lists(self):
        mock_result = MagicMock()
        mock_result.get_counts_list.return_value = []
        mock_result.get_probs_list.return_value = []

        counts, probs = OriginJob._extract_results(mock_result)
        assert counts is None
        assert probs is None

    def test_passes_through_sdk_types(self):
        mock_result = MagicMock()
        mock_result.get_counts_list.return_value = [{"00": 500, "11": 500}]
        mock_result.get_probs_list.return_value = [{"00": 0.5, "11": 0.5}]

        counts, probs = OriginJob._extract_results(mock_result)
        assert counts == {"00": 500, "11": 500}
        assert probs == {"00": 0.5, "11": 0.5}


# --- _get_job reconstruction path ---


class TestGetJobReconstruction:
    @patch("pyqpanda3.qcloud.QCloudJob")
    @patch("pyqpanda3.qcloud.QCloudService")
    def test_get_job_no_service_creates_service_from_env(
        self, mock_service_cls, mock_job_cls, monkeypatch
    ):
        monkeypatch.setenv("ORIGIN_API_KEY", "test-key")
        mock_qcloud_job = MagicMock()
        mock_job_cls.return_value = mock_qcloud_job

        result = OriginJob._get_job("job-123", job=None, service=None)

        mock_service_cls.assert_called_once_with("test-key")
        mock_job_cls.assert_called_once_with("job-123")
        assert result is mock_qcloud_job

    @patch("pyqpanda3.qcloud.QCloudJob")
    @patch("pyqpanda3.qcloud.QCloudService")
    def test_get_job_with_service_skips_env(self, mock_service_cls, mock_job_cls):
        mock_qcloud_job = MagicMock()
        mock_job_cls.return_value = mock_qcloud_job
        mock_service = MagicMock()

        result = OriginJob._get_job("job-123", job=None, service=mock_service)

        mock_service_cls.assert_not_called()
        mock_job_cls.assert_called_once_with("job-123")
        assert result is mock_qcloud_job

    @patch("pyqpanda3.qcloud.QCloudJob")
    @patch("pyqpanda3.qcloud.QCloudService")
    def test_get_job_reconstruction_failure_raises(self, _mock_service_cls, mock_job_cls):
        mock_job_cls.side_effect = RuntimeError("connection failed")

        with pytest.raises(OriginJobError, match="Unable to retrieve OriginQ job"):
            OriginJob._get_job("bad-id", job=None, service=MagicMock())


# --- _get_service ---


class TestGetService:
    @patch("pyqpanda3.qcloud.QCloudService")
    def test_get_service(self, mock_service_cls):
        mock_instance = MagicMock()
        mock_service_cls.return_value = mock_instance

        result = _get_service("my-api-key")

        mock_service_cls.assert_called_once_with(api_key="my-api-key")
        assert result is mock_instance


# --- _infer_basis_gates exception path ---


class TestInferBasisGates:
    def test_infer_basis_gates_exception_returns_none(self):
        mock_backend = MagicMock()
        mock_backend.name.return_value = "WK_C180"
        mock_backend.chip_info.side_effect = RuntimeError("unavailable")

        assert _infer_basis_gates(mock_backend) is None

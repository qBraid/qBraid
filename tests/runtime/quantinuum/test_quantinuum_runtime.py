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
Unit tests for Quantinuum provider, device, and job classes.

"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("qnexus", reason="qnexus is not installed.")
pytest.importorskip("pytket", reason="pytket is not installed.")

# pylint: disable=wrong-import-position
from qbraid.runtime.enums import DeviceStatus, JobStatus  # noqa: E402
from qbraid.runtime.exceptions import ResourceNotFoundError  # noqa: E402
from qbraid.runtime.quantinuum import (  # noqa: E402
    QuantinuumDevice,
    QuantinuumJob,
    QuantinuumProvider,
)
from qbraid.runtime.quantinuum.device import QuantinuumDeviceError  # noqa: E402
from qbraid.runtime.quantinuum.job import (  # noqa: E402
    _QUANTINUUM_STATUS_MAP,
    QuantinuumJobError,
    _map_quantinuum_status,
)

# --- Status mapping ---


class TestStatusMapping:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("COMPLETED", JobStatus.COMPLETED),
            ("ERROR", JobStatus.FAILED),
            ("CANCELLED", JobStatus.CANCELLED),
            ("QUEUED", JobStatus.QUEUED),
            ("RUNNING", JobStatus.RUNNING),
            ("INITIALIZING", JobStatus.INITIALIZING),
            ("UNEXPECTED_VALUE", JobStatus.UNKNOWN),
            (None, JobStatus.UNKNOWN),
        ],
    )
    def test_map_quantinuum_status(self, raw, expected):
        assert _map_quantinuum_status(raw) == expected

    def test_status_map_covers_expected_states(self):
        expected = {"COMPLETED", "ERROR", "CANCELLED", "QUEUED", "RUNNING", "INITIALIZING"}
        assert set(_QUANTINUUM_STATUS_MAP.keys()) == expected


# --- Provider ---


def _make_backend_info(num_qubits: int = 20, version: str = "2.0.0"):
    """Build a mock pytket BackendInfo-like object."""
    backend_info = MagicMock()
    backend_info.architecture.nodes = list(range(num_qubits))
    backend_info.version = version
    return backend_info


class TestQuantinuumProvider:
    @patch("qnexus.devices.get_all")
    def test_get_device(self, mock_get_all):
        backend_info = _make_backend_info()
        df_mock = MagicMock()
        df_mock.loc.__getitem__.return_value.empty = False
        row = MagicMock()
        row.__getitem__.return_value = backend_info
        df_mock.loc.__getitem__.return_value.iloc.__getitem__.return_value = row
        mock_get_all.return_value.df.return_value = df_mock

        provider = QuantinuumProvider()
        device = provider.get_device("H1-1E")

        assert isinstance(device, QuantinuumDevice)
        assert device.id == "H1-1E"
        assert device.profile.simulator is True

    @patch("qnexus.devices.get_all")
    def test_get_device_not_found_raises(self, mock_get_all):
        df_mock = MagicMock()
        df_mock.loc.__getitem__.return_value.empty = True
        df_mock.__getitem__.return_value.tolist.return_value = ["H2-1"]
        mock_get_all.return_value.df.return_value = df_mock

        provider = QuantinuumProvider()

        with pytest.raises(ResourceNotFoundError, match="not found"):
            provider.get_device("H9-9")


# --- Device ---


def _make_device(device_id: str = "H1-1E", simulator: bool = True):
    """Helper to create a QuantinuumDevice with a mocked profile."""
    backend_info = _make_backend_info()
    profile = MagicMock()
    profile.device_id = device_id
    profile.simulator = simulator
    profile.backend_info = backend_info
    device = QuantinuumDevice(profile=profile)
    # QuantumDevice.id is a property that returns profile.device_id
    type(device).id = property(lambda self: self.profile.device_id)
    return device


class TestQuantinuumDevice:
    def test_str_representation(self):
        device = _make_device()
        assert "QuantinuumDevice" in str(device)
        assert "H1-1E" in str(device)

    def test_backend_info_accessor(self):
        device = _make_device()
        assert device.backend_info is device.profile.backend_info

    @patch("qnexus.devices.status")
    @patch("qnexus.models.QuantinuumConfig")
    def test_status_online(self, _mock_config, mock_status):
        # pylint: disable-next=import-outside-toplevel
        from qnexus.client.devices import DeviceStateEnum

        mock_status.return_value = DeviceStateEnum.ONLINE
        device = _make_device()
        assert device.status() == DeviceStatus.ONLINE

    @patch("qnexus.devices.status")
    @patch("qnexus.models.QuantinuumConfig")
    def test_status_reserved_online(self, _mock_config, mock_status):
        # pylint: disable-next=import-outside-toplevel
        from qnexus.client.devices import DeviceStateEnum

        mock_status.return_value = DeviceStateEnum.RESERVED_ONLINE
        device = _make_device()
        assert device.status() == DeviceStatus.ONLINE

    @patch("qnexus.devices.status")
    @patch("qnexus.models.QuantinuumConfig")
    def test_status_maintenance(self, _mock_config, mock_status):
        # pylint: disable-next=import-outside-toplevel
        from qnexus.client.devices import DeviceStateEnum

        mock_status.return_value = DeviceStateEnum.MAINTENANCE
        device = _make_device()
        assert device.status() == DeviceStatus.UNAVAILABLE

    @patch("qnexus.devices.status")
    @patch("qnexus.models.QuantinuumConfig")
    def test_status_offline(self, _mock_config, mock_status):
        mock_status.return_value = "OFFLINE"  # any other value
        device = _make_device()
        assert device.status() == DeviceStatus.OFFLINE


# --- Job ---


class TestQuantinuumJob:
    def test_status_completed(self):
        mock_ref = SimpleNamespace(last_status="COMPLETED")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        assert job.status() == JobStatus.COMPLETED

    def test_status_running(self):
        mock_ref = SimpleNamespace(last_status="RUNNING")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        assert job.status() == JobStatus.RUNNING

    def test_status_queued(self):
        mock_ref = SimpleNamespace(last_status="QUEUED")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        assert job.status() == JobStatus.QUEUED

    def test_status_failed_logs_message(self, caplog):
        mock_ref = SimpleNamespace(last_status="ERROR", last_message="compilation failed")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        with caplog.at_level("ERROR"):
            assert job.status() == JobStatus.FAILED
        assert "compilation failed" in caplog.text

    def test_status_caches_terminal(self):
        mock_ref = SimpleNamespace(last_status="COMPLETED")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        job.status()
        # Subsequent calls use cached value
        mock_ref.last_status = "RUNNING"
        assert job.status() == JobStatus.COMPLETED

    def test_status_unknown_on_missing_attribute(self):
        mock_ref = SimpleNamespace()  # no last_status attribute
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        assert job.status() == JobStatus.UNKNOWN

    @patch("qnexus.jobs.cancel")
    def test_cancel(self, mock_cancel):
        mock_ref = SimpleNamespace(last_status="RUNNING")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        job.cancel()
        mock_cancel.assert_called_once_with(mock_ref)

    @patch("qnexus.jobs.cancel")
    def test_cancel_error_raises(self, mock_cancel):
        mock_cancel.side_effect = RuntimeError("API error")
        mock_ref = SimpleNamespace(last_status="RUNNING")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        with pytest.raises(QuantinuumJobError, match="Failed to cancel"):
            job.cancel()

    def test_execution_time_not_completed(self):
        mock_ref = SimpleNamespace(last_status="RUNNING")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        assert job.execution_time_s() is None

    def test_execution_time_computes_delta(self):
        start = datetime.now(timezone.utc)
        end = start + timedelta(seconds=42)
        mock_ref = SimpleNamespace(
            last_status="COMPLETED",
            last_status_detail=SimpleNamespace(running_time=start, completed_time=end),
        )
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        assert job.execution_time_s() == pytest.approx(42.0)

    def test_execution_time_missing_detail_raises(self):
        mock_ref = SimpleNamespace(last_status="COMPLETED", last_status_detail=None)
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        with pytest.raises(QuantinuumJobError, match="last_status_detail is missing"):
            job.execution_time_s()

    def test_execution_time_missing_timestamps_raises(self):
        mock_ref = SimpleNamespace(
            last_status="COMPLETED",
            last_status_detail=SimpleNamespace(running_time=None, completed_time=None),
        )
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        with pytest.raises(QuantinuumJobError, match="completed_time or running_time is missing"):
            job.execution_time_s()

    def test_result_failed_job_raises(self):
        mock_ref = SimpleNamespace(last_status="ERROR", last_message="segfault")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        with pytest.raises(QuantinuumJobError, match="segfault"):
            job.result()

    @patch("qnexus.jobs.results")
    def test_result_single_circuit(self, mock_results):
        # pylint: disable-next=import-outside-toplevel
        from pytket.circuit import BasisOrder

        download = MagicMock()
        download.get_counts.return_value = {(0, 0): 512, (1, 1): 488}
        result_item = MagicMock()
        result_item.download_result.return_value = download
        mock_results.return_value = [result_item]

        mock_ref = SimpleNamespace(last_status="COMPLETED")
        mock_device = MagicMock()
        mock_device.id = "H1-1E"

        job = QuantinuumJob(job_id="job-123", device=mock_device, job=mock_ref)
        result = job.result()

        assert result.success is True
        assert result.data.measurement_counts == {"00": 512, "11": 488}
        download.get_counts.assert_called_once_with(basis=BasisOrder.dlo)

    @patch("qnexus.jobs.results")
    def test_result_batch(self, mock_results):
        def make_item(counts):
            download = MagicMock()
            download.get_counts.return_value = counts
            item = MagicMock()
            item.download_result.return_value = download
            return item

        mock_results.return_value = [
            make_item({(0, 0): 100}),
            make_item({(1, 1): 100}),
        ]

        mock_ref = SimpleNamespace(last_status="COMPLETED")
        mock_device = MagicMock()
        mock_device.id = "H1-1E"

        job = QuantinuumJob(job_id="job-123", device=mock_device, job=mock_ref)
        result = job.result()

        assert result.data.measurement_counts == [{"00": 100}, {"11": 100}]

    @patch("qnexus.jobs.results")
    def test_result_empty_raises(self, mock_results):
        mock_results.return_value = []
        mock_ref = SimpleNamespace(last_status="COMPLETED")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        with pytest.raises(QuantinuumJobError, match="No results available"):
            job.result()

    @patch("qnexus.jobs.results")
    def test_result_derives_device_id_from_job_metadata(self, mock_results):
        """When no device is attached, prefer the device_name recorded on the job ref."""
        download = MagicMock()
        download.get_counts.return_value = {(0, 0): 10}
        result_item = MagicMock()
        result_item.download_result.return_value = download
        mock_results.return_value = [result_item]

        mock_ref = SimpleNamespace(
            last_status="COMPLETED",
            backend_config_store=SimpleNamespace(device_name="H2-1"),
        )
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        result = job.result()
        assert result.device_id == "H2-1"

    @patch("qnexus.jobs.results")
    def test_result_falls_back_to_generic_device_id(self, mock_results):
        """Fallback label when neither device nor backend_config_store is available."""
        download = MagicMock()
        download.get_counts.return_value = {(0, 0): 10}
        result_item = MagicMock()
        result_item.download_result.return_value = download
        mock_results.return_value = [result_item]

        mock_ref = SimpleNamespace(last_status="COMPLETED")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        result = job.result()
        assert result.device_id == "quantinuum"


# Silence unused-import warnings from conditional imports referenced only in tests.
_ = QuantinuumDeviceError

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

    @patch("qnexus.devices.get_all")
    def test_get_devices_makes_single_remote_call(self, mock_get_all):
        """Regression test: ``get_devices`` must not re-fetch the device list
        once per row (the earlier N+1 pattern that round-tripped through
        ``get_device``/``_get_backend_info``)."""
        backend_info = _make_backend_info()
        row_a = {"device_name": "H1-1E", "backend_info": backend_info}
        row_b = {"device_name": "H2-1", "backend_info": backend_info}

        df_mock = MagicMock()
        df_mock.iterrows.return_value = iter([(0, row_a), (1, row_b)])
        mock_get_all.return_value.df.return_value = df_mock

        provider = QuantinuumProvider()
        devices = provider.get_devices()

        assert {d.id for d in devices} == {"H1-1E", "H2-1"}
        # Single API call for the entire list, not one-per-row.
        mock_get_all.assert_called_once()

    def test_provider_is_hashable(self):
        """``QuantinuumProvider`` instances must be hashable for ``cached_method``."""
        provider_a = QuantinuumProvider()
        provider_b = QuantinuumProvider()

        # ``hash()`` succeeds and each instance is independent.
        assert hash(provider_a) == hash(provider_a)
        assert hash(provider_a) != hash(provider_b)
        # Usable as a dict key / set member.
        assert len({provider_a, provider_b}) == 2


# --- Device ---


def _make_device(device_id: str = "H1-1E", simulator: bool = True):
    """Helper to create a QuantinuumDevice with a mocked profile.

    The base :class:`QuantumDevice.id` property reads ``self.profile.device_id``,
    so we just configure the mocked profile accordingly.
    """
    backend_info = _make_backend_info()
    profile = MagicMock()
    profile.device_id = device_id
    profile.simulator = simulator
    profile.backend_info = backend_info
    return QuantinuumDevice(profile=profile)


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

    @patch("qnexus.start_execute_job")
    @patch("qnexus.jobs.results")
    @patch("qnexus.jobs.wait_for")
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_runs_full_compile_execute_pipeline(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        mock_compile,
        _mock_wait,
        mock_results,
        mock_execute,
    ):
        """``submit`` must upload circuits, compile, fetch compiled refs, then execute."""
        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        compiled_item = MagicMock()
        compiled_item.get_output.return_value = MagicMock(name="compiled-ref")
        mock_results.return_value = [compiled_item]
        mock_upload.side_effect = [MagicMock(name="circuit-ref")]
        execute_job_id = "00000000-0000-0000-0000-000000000001"
        mock_execute.return_value = MagicMock(id=execute_job_id)

        device = _make_device()
        circuit = Circuit(2)
        job = device.submit(circuit, shots=500)

        # One circuit uploaded.
        assert mock_upload.call_count == 1
        # Compile then execute.
        mock_compile.assert_called_once()
        mock_execute.assert_called_once()
        _, execute_kwargs = mock_execute.call_args
        assert execute_kwargs["n_shots"] == [500]
        assert isinstance(job, QuantinuumJob)
        assert job.id == execute_job_id

    @patch("qnexus.start_execute_job")
    @patch("qnexus.jobs.results")
    @patch("qnexus.jobs.wait_for")
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_accepts_project_and_opt_level_kwargs(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        mock_compile,
        _mock_wait,
        mock_results,
        mock_execute,
    ):
        """``submit`` should honor ``project_name``/``optimisation_level`` kwargs."""
        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        compiled_item = MagicMock()
        compiled_item.get_output.return_value = MagicMock(name="compiled-ref")
        mock_results.return_value = [compiled_item]
        mock_upload.side_effect = [MagicMock(name="circuit-ref")]
        mock_execute.return_value = MagicMock(id="job-id")

        device = _make_device()
        device.submit(Circuit(2), shots=100, project_name="my-proj", optimisation_level=2)

        mock_get_or_create.assert_called_once_with(name="my-proj")
        _, compile_kwargs = mock_compile.call_args
        assert compile_kwargs["optimisation_level"] == 2


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

    def test_status_unknown_on_unrecognized_value(self):
        """An unexpected ``last_status`` string maps to UNKNOWN rather than raising."""
        mock_ref = SimpleNamespace(last_status="SOMETHING_UNEXPECTED")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        assert job.status() == JobStatus.UNKNOWN

    def test_status_wraps_ref_lookup_errors(self):
        """Exceptions raised when accessing the job ref are wrapped as QuantinuumJobError."""

        class BadRef:
            @property
            def last_status(self):
                raise RuntimeError("connection lost")

        job = QuantinuumJob(job_id="job-123", job=BadRef())
        with pytest.raises(QuantinuumJobError, match="Unable to retrieve job status"):
            job.status()

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

    @patch("qnexus.jobs.get")
    def test_get_ref_lazily_fetches_when_job_is_none(self, mock_get):
        """When no job ref was supplied, ``_get_ref`` should look it up by ID."""
        fetched_ref = SimpleNamespace(last_status="QUEUED")
        mock_get.return_value = fetched_ref

        job = QuantinuumJob(job_id="job-123")
        ref = job._get_ref()  # pylint: disable=protected-access

        mock_get.assert_called_once_with(id="job-123")
        assert ref is fetched_ref
        # Cached for subsequent calls.
        assert job._get_ref() is fetched_ref  # pylint: disable=protected-access
        mock_get.assert_called_once()

    @patch("qnexus.jobs.get")
    def test_get_ref_wraps_remote_errors(self, mock_get):
        """Remote lookup failures are surfaced as QuantinuumJobError."""
        mock_get.side_effect = RuntimeError("nexus down")

        job = QuantinuumJob(job_id="job-123")
        with pytest.raises(QuantinuumJobError, match="Unable to retrieve Quantinuum job"):
            job._get_ref()  # pylint: disable=protected-access

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
    def test_result_wraps_remote_errors(self, mock_results):
        """Errors from ``qnx.jobs.results`` should surface as QuantinuumJobError."""
        mock_results.side_effect = RuntimeError("nexus timeout")
        mock_ref = SimpleNamespace(last_status="COMPLETED")
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        with pytest.raises(QuantinuumJobError, match="Failed to fetch results"):
            job.result()

    @patch("qnexus.jobs.results")
    def test_result_derives_device_id_from_job_metadata(self, mock_results):
        """When no device is attached, prefer the device_name recorded on the job ref."""
        # pylint: disable-next=import-outside-toplevel
        from quantinuum_schemas.models.backend_config import QuantinuumConfig

        download = MagicMock()
        download.get_counts.return_value = {(0, 0): 10}
        result_item = MagicMock()
        result_item.download_result.return_value = download
        mock_results.return_value = [result_item]

        mock_ref = SimpleNamespace(
            last_status="COMPLETED",
            backend_config=QuantinuumConfig(device_name="H2-1"),
        )
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        result = job.result()
        assert result.device_id == "H2-1"

    @patch("qnexus.jobs.results")
    def test_result_falls_back_to_generic_device_id(self, mock_results):
        """Fallback label when backend_config is not a QuantinuumConfig."""
        # pylint: disable-next=import-outside-toplevel
        from quantinuum_schemas.models.backend_config import AerConfig

        download = MagicMock()
        download.get_counts.return_value = {(0, 0): 10}
        result_item = MagicMock()
        result_item.download_result.return_value = download
        mock_results.return_value = [result_item]

        mock_ref = SimpleNamespace(last_status="COMPLETED", backend_config=AerConfig())
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        result = job.result()
        assert result.device_id == "quantinuum"


# Silence unused-import warnings from conditional imports referenced only in tests.
_ = QuantinuumDeviceError

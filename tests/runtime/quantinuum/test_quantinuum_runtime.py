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
# pylint: disable=too-many-public-methods,too-many-arguments,too-many-lines

"""
Unit tests for Quantinuum provider, device, and job classes.

"""
import importlib
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


def _import_or_skip(name: str):
    """Skip the module only when ``name`` itself is not installed.

    ``pytest.importorskip`` swallows any ImportError, including one raised
    from inside an installed package. That is how qnexus 0.48.0, which
    imports the undeclared ``selene_core``, silently skipped this entire
    file in CI: every job stayed green while patch coverage read 0%. A
    broken dependency should fail loudly; only a genuinely absent one may
    skip.
    """
    try:
        importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            pytest.skip(f"{name} is not installed.", allow_module_level=True)
        raise


_import_or_skip("qnexus")
_import_or_skip("pytket")

# pylint: disable=wrong-import-position
from qbraid.runtime.enums import DeviceStatus, JobStatus  # noqa: E402
from qbraid.runtime.exceptions import ResourceNotFoundError  # noqa: E402
from qbraid.runtime.profile import TargetProfile  # noqa: E402
from qbraid.runtime.quantinuum import (  # noqa: E402
    QuantinuumDevice,
    QuantinuumJob,
    QuantinuumProvider,
)
from qbraid.runtime.quantinuum._transport import (  # noqa: E402
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    ensure_bounded_client,
    retry_transient,
)
from qbraid.runtime.quantinuum.device import (  # noqa: E402
    DEFAULT_COMPILE_TIMEOUT_SECONDS,
    QuantinuumDeviceError,
)
from qbraid.runtime.quantinuum.job import (  # noqa: E402
    _QUANTINUUM_STATUS_MAP,
    QuantinuumJobError,
    _map_quantinuum_status,
)
from qbraid.runtime.quantinuum.provider import _is_simulator  # noqa: E402

# --- Status mapping ---


class TestStatusMapping:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("COMPLETED", JobStatus.COMPLETED),
            ("ERROR", JobStatus.FAILED),
            ("TERMINATED", JobStatus.FAILED),
            ("DEPLETED", JobStatus.FAILED),
            ("CANCELLED", JobStatus.CANCELLED),
            ("CANCELLING", JobStatus.CANCELLING),
            ("SUBMITTED", JobStatus.QUEUED),
            ("QUEUED", JobStatus.QUEUED),
            ("RETRYING", JobStatus.QUEUED),
            ("RUNNING", JobStatus.RUNNING),
            ("UNEXPECTED_VALUE", JobStatus.UNKNOWN),
            (None, JobStatus.UNKNOWN),
        ],
    )
    def test_map_quantinuum_status(self, raw, expected):
        assert _map_quantinuum_status(raw) == expected

    def test_status_map_covers_every_nexus_status(self):
        """The map must cover all of qnexus's statuses, checked against qnexus.

        Asserting the map equals a hand-written copy of itself proves nothing:
        it stays green no matter which states are missing. Unmapped statuses
        fall through to ``UNKNOWN``, which is not terminal, so a NEXUS state
        that has actually stopped the job would be polled forever.
        """
        # pylint: disable-next=import-outside-toplevel
        from qnexus.models.job_status import JobStatusEnum

        nexus_statuses = {member.value for member in JobStatusEnum}
        assert set(_QUANTINUUM_STATUS_MAP) == nexus_statuses

    def test_terminal_nexus_states_map_to_terminal_qbraid_states(self):
        """NEXUS states that stop a job must not map to a pollable status."""
        for raw in ("COMPLETED", "ERROR", "CANCELLED", "TERMINATED", "DEPLETED"):
            assert _map_quantinuum_status(raw) in JobStatus.terminal_states()


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
        row = {"backend_info": backend_info, "nexus_hosted": True}
        df_mock.loc.__getitem__.return_value.iloc.__getitem__.return_value = row
        mock_get_all.return_value.df.return_value = df_mock

        provider = QuantinuumProvider()
        device = provider.get_device("H1-1E")

        assert isinstance(device, QuantinuumDevice)
        assert device.id == "H1-1E"
        assert device.profile.simulator is True
        assert device.profile.nexus_hosted is True

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
        ``get_device``/``_get_device_entry``)."""
        backend_info = _make_backend_info()
        row_a = {"device_name": "H1-1E", "backend_info": backend_info, "nexus_hosted": True}
        row_b = {"device_name": "H2-1", "backend_info": backend_info, "nexus_hosted": False}

        df_mock = MagicMock()
        df_mock.iterrows.return_value = iter([(0, row_a), (1, row_b)])
        mock_get_all.return_value.df.return_value = df_mock

        provider = QuantinuumProvider()
        devices = provider.get_devices()

        assert {d.id for d in devices} == {"H1-1E", "H2-1"}
        # Per-row nexus_hosted flags propagate into each device's profile.
        assert {d.id: d.profile.nexus_hosted for d in devices} == {"H1-1E": True, "H2-1": False}
        # Single API call for the entire list, not one-per-row.
        mock_get_all.assert_called_once()

    @pytest.mark.parametrize(
        ("device_name", "nexus_hosted", "expected"),
        [
            # Hardware. "Helios-1" is the case a substring test for "E" gets
            # wrong: it would mark a QPU as a simulator.
            ("H1-1", False, False),
            ("H2-1", False, False),
            ("Helios-1", False, False),
            # Device-hosted emulator, syntax checker, Nexus-hosted emulator.
            ("H1-1E", False, True),
            ("H2-1SC", False, True),
            ("H1-1LE", True, True),
            ("H2-Emulator", True, True),
        ],
    )
    def test_simulator_classification(self, device_name, nexus_hosted, expected):
        assert _is_simulator(device_name, nexus_hosted) is expected

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


def _make_device(device_id: str = "H1-1E", simulator: bool = True, nexus_hosted: bool = False):
    """Helper to create a QuantinuumDevice with a mocked profile.

    The base :class:`QuantumDevice.id` property reads ``self.profile.device_id``,
    so we just configure the mocked profile accordingly.
    """
    backend_info = _make_backend_info()
    profile = MagicMock()
    profile.device_id = device_id
    profile.simulator = simulator
    profile.backend_info = backend_info
    profile.nexus_hosted = nexus_hosted
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
    def test_status_nexus_hosted_always_online(self, _mock_config, mock_status):
        """Cloud-hosted emulators (e.g. 'H2-Emulator') have no machine status
        endpoint (it 400s with 'Invalid machine name'), so they must report
        ONLINE without calling it."""
        device = _make_device(device_id="H2-Emulator", nexus_hosted=True)
        assert device.status() == DeviceStatus.ONLINE
        mock_status.assert_not_called()

    @patch("qnexus.devices.status")
    @patch("qnexus.models.QuantinuumConfig")
    def test_status_missing_nexus_hosted_falls_back_to_endpoint(self, _mock_config, mock_status):
        """Profiles built before the ``nexus_hosted`` extra existed (e.g. cached
        or hand-constructed) must keep the pre-fix behavior of querying the
        machine status endpoint. Uses a real ``TargetProfile`` because a
        ``MagicMock`` profile would auto-create the attribute."""
        # pylint: disable-next=import-outside-toplevel
        from qnexus.client.devices import DeviceStateEnum

        mock_status.return_value = DeviceStateEnum.ONLINE
        profile = TargetProfile(device_id="H1-1", simulator=False)
        device = QuantinuumDevice(profile=profile)

        assert device.status() == DeviceStatus.ONLINE
        mock_status.assert_called_once()

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

    @patch("qnexus.jobs.wait_for")
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_compile_wait_is_bounded(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        mock_compile,
        mock_wait,
    ):
        """The compile wait passes a timeout and surfaces expiry as a device error.

        An unbounded ``wait_for`` leaks the calling thread forever if the NEXUS
        compile job hangs, which starves thread pools in server deployments.
        """
        # pylint: disable-next=import-outside-toplevel
        import asyncio

        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        mock_upload.side_effect = [MagicMock(name="circuit-ref")]
        mock_wait.side_effect = asyncio.TimeoutError()

        device = _make_device()
        with pytest.raises(QuantinuumDeviceError, match="did not complete within 900"):
            device.submit(Circuit(2), shots=100)

        _, wait_kwargs = mock_wait.call_args
        assert wait_kwargs["timeout"] == DEFAULT_COMPILE_TIMEOUT_SECONDS

    @patch("qbraid.runtime.quantinuum._transport.time.sleep")
    @patch("qnexus.start_execute_job")
    @patch("qnexus.jobs.results")
    @patch("qnexus.jobs.wait_for")
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_retries_transient_upload_errors(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        mock_compile,
        _mock_wait,
        mock_results,
        mock_execute,
        _mock_sleep,
    ):
        """Pre-execute stages retry on transient NEXUS connection errors."""
        # pylint: disable-next=import-outside-toplevel
        import httpx

        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        compiled_item = MagicMock()
        compiled_item.get_output.return_value = MagicMock(name="compiled-ref")
        mock_results.return_value = [compiled_item]
        # First upload attempt drops the connection; the retry succeeds.
        mock_upload.side_effect = [
            httpx.RemoteProtocolError("Server disconnected without sending a response."),
            MagicMock(name="circuit-ref"),
        ]
        mock_execute.return_value = MagicMock(id="job-id")

        device = _make_device()
        job = device.submit(Circuit(2), shots=100)

        assert mock_upload.call_count == 2
        assert isinstance(job, QuantinuumJob)
        # The execute dispatch itself must never be retried (double-submit risk),
        # so it is called exactly once.
        mock_execute.assert_called_once()

    @patch.dict(os.environ, {"QUANTINUUM_NEXUS_COMPILE_TIMEOUT": "120"})
    @patch("qnexus.jobs.wait_for")
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_compile_timeout_env_override(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        mock_compile,
        mock_wait,
    ):
        """QUANTINUUM_NEXUS_COMPILE_TIMEOUT overrides the default compile bound."""
        # pylint: disable-next=import-outside-toplevel
        import asyncio

        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        mock_upload.side_effect = [MagicMock(name="circuit-ref")]
        mock_wait.side_effect = asyncio.TimeoutError()

        device = _make_device()
        with pytest.raises(QuantinuumDeviceError, match="within 120"):
            device.submit(Circuit(2), shots=100)

        assert mock_wait.call_args.kwargs["timeout"] == 120.0

    @pytest.mark.skipif(
        not hasattr(importlib.import_module("qnexus.client.jobs"), "HybridStrategy"),
        reason="qnexus predates WaitStrategy classes (added after 0.39); "
        "wait_for has no strategy to hang there, so the fabricated-exception "
        "tests are the only pin available.",
    )
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_maps_real_wait_for_expiry(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        mock_compile,
    ):
        """A genuine ``qnx.jobs.wait_for`` expiry maps to ``QuantinuumDeviceError``.

        The other timeout tests fabricate the exception and then assert the
        mapping of their own fabrication, so they would stay green if upstream
        switched to a custom timeout type. This one drives the real
        ``wait_for`` with a strategy that never returns, pinning the assumption
        that expiry surfaces as ``asyncio.TimeoutError``.
        """
        # pylint: disable-next=import-outside-toplevel
        import asyncio

        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        class _HangingStrategy:
            """Wait strategy that never reaches a terminal status."""

            async def get_status(self, _job):
                """Block until the caller's timeout expires."""
                await asyncio.sleep(60)

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        mock_upload.side_effect = [MagicMock(name="circuit-ref")]

        device = _make_device()
        with (
            patch.dict(os.environ, {"QUANTINUUM_NEXUS_COMPILE_TIMEOUT": "0.05"}),
            patch("qnexus.client.jobs.HybridStrategy", _HangingStrategy),
            pytest.raises(QuantinuumDeviceError, match="did not complete within"),
        ):
            device.submit(Circuit(2), shots=100)

    @patch("qnexus.jobs.wait_for")
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_wraps_compile_job_error(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        mock_compile,
        mock_wait,
    ):
        """A compile that errors or is cancelled surfaces as a qBraid error.

        ``wait_for`` raises ``qnx_exc.JobError`` in that case; left unwrapped it
        escapes ``submit`` as a bare qnexus exception.
        """
        # pylint: disable-next=import-outside-toplevel
        import qnexus.exceptions as qnx_exc

        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        mock_upload.side_effect = [MagicMock(name="circuit-ref")]
        mock_wait.side_effect = qnx_exc.JobError("Job errored: unsupported gate")

        device = _make_device()
        with pytest.raises(QuantinuumDeviceError, match="did not succeed"):
            device.submit(Circuit(2), shots=100)

    @patch("qbraid.runtime.quantinuum._transport.time.sleep")
    @patch("qnexus.start_execute_job")
    @patch("qnexus.jobs.results")
    @patch("qnexus.jobs.wait_for")
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_retries_lazy_compiled_output_fetch(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        mock_compile,
        _mock_wait,
        mock_results,
        mock_execute,
        _mock_sleep,
    ):
        """``get_output`` is lazy, so the whole fetch stage must sit in the retry.

        ``CompilationResultRef.get_output`` issues its own NEXUS request; if only
        ``jobs.results`` were wrapped, a blip there would propagate unretried.
        """
        # pylint: disable-next=import-outside-toplevel
        import httpx

        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        mock_upload.side_effect = [MagicMock(name="circuit-ref")]
        compiled_item = MagicMock()
        compiled_item.get_output.side_effect = [
            httpx.RemoteProtocolError("Server disconnected without sending a response."),
            MagicMock(name="compiled-ref"),
        ]
        mock_results.return_value = [compiled_item]
        mock_execute.return_value = MagicMock(id="job-id")

        device = _make_device()
        job = device.submit(Circuit(2), shots=100)

        assert compiled_item.get_output.call_count == 2
        assert isinstance(job, QuantinuumJob)

    @patch("qbraid.runtime.quantinuum._transport.time.sleep")
    @patch("qnexus.start_execute_job")
    @patch("qnexus.jobs.results")
    @patch("qnexus.jobs.wait_for")
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_retries_nexus_gateway_errors(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        mock_compile,
        _mock_wait,
        mock_results,
        mock_execute,
        _mock_sleep,
    ):
        """A NEXUS 503 is retried.

        qnexus checks status codes by hand and raises its own exception types
        rather than letting httpx raise ``HTTPStatusError``, so a gateway blip
        never appears as a ``TransportError``.
        """
        # pylint: disable-next=import-outside-toplevel
        import qnexus.exceptions as qnx_exc

        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        compiled_item = MagicMock()
        compiled_item.get_output.return_value = MagicMock(name="compiled-ref")
        mock_results.return_value = [compiled_item]
        mock_upload.side_effect = [
            qnx_exc.ResourceCreateFailed(message="upstream unavailable", status_code=503),
            MagicMock(name="circuit-ref"),
        ]
        mock_execute.return_value = MagicMock(id="job-id")

        device = _make_device()
        job = device.submit(Circuit(2), shots=100)

        assert mock_upload.call_count == 2
        assert isinstance(job, QuantinuumJob)

    @patch("qbraid.runtime.quantinuum._transport.time.sleep")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_does_not_retry_client_errors(
        self,
        mock_get_or_create,
        _mock_config,
        mock_upload,
        _mock_sleep,
    ):
        """A rejected program (4xx) is a real failure and must surface at once."""
        # pylint: disable-next=import-outside-toplevel
        import qnexus.exceptions as qnx_exc

        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_upload.side_effect = qnx_exc.ResourceCreateFailed(
            message="circuit too wide for device", status_code=400
        )

        device = _make_device()
        with pytest.raises(qnx_exc.ResourceCreateFailed):
            device.submit(Circuit(2), shots=100)

        assert mock_upload.call_count == 1

    @patch("qnexus.start_execute_job")
    @patch("qnexus.jobs.results")
    @patch("qnexus.jobs.wait_for")
    @patch("qnexus.start_compile_job")
    @patch("qnexus.circuits.upload")
    @patch("qnexus.QuantinuumConfig")
    @patch("qnexus.projects.get_or_create")
    def test_submit_wraps_execute_dispatch_timeout(
        self,
        mock_get_or_create,
        _mock_config,
        _mock_upload,
        mock_compile,
        _mock_wait,
        mock_results,
        mock_execute,
    ):
        """A timeout on the execute dispatch names the possibly-orphaned job.

        The dispatch is never retried (double-submit risk), but with the shared
        client bounded, a slow NEXUS response now times out after the server
        may already have accepted a billable job. A bare ``httpx.ReadTimeout``
        gives the caller nothing to find that job with; the wrapped error must
        say which project to search and what the job is named.
        """
        # pylint: disable-next=import-outside-toplevel
        import httpx

        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        mock_get_or_create.return_value = MagicMock(name="project")
        mock_compile.return_value = MagicMock(id="compile-job-id")
        compiled_item = MagicMock()
        compiled_item.get_output.return_value = MagicMock(name="compiled-ref")
        mock_results.return_value = [compiled_item]
        mock_execute.side_effect = httpx.ReadTimeout("timed out")

        device = _make_device()
        with pytest.raises(
            QuantinuumDeviceError, match=r"check project 'qbraid' for a job named 'qbraid execute"
        ):
            device.submit(Circuit(2), shots=100)

        # Ambiguous acceptance: exactly one dispatch attempt, never a retry.
        mock_execute.assert_called_once()

    @pytest.mark.parametrize(
        ("env", "value", "match"),
        [
            ("QUANTINUUM_NEXUS_COMPILE_TIMEOUT", "15m", "must be a number of seconds"),
            ("QUANTINUUM_NEXUS_COMPILE_TIMEOUT", "0", "must be positive"),
            ("QUANTINUUM_NEXUS_COMPILE_TIMEOUT", "-5", "must be positive"),
            # float() accepts these and every comparison against NaN is false,
            # so a bare `value <= 0` guard lets them through.
            ("QUANTINUUM_NEXUS_COMPILE_TIMEOUT", "nan", "must be a finite number"),
            ("QUANTINUUM_NEXUS_COMPILE_TIMEOUT", "inf", "must be a finite number"),
            ("QUANTINUUM_NEXUS_HTTP_TIMEOUT", "abc", "must be a number of seconds"),
            ("QUANTINUUM_NEXUS_OPT_LEVEL", "high", "must be an integer"),
            ("QUANTINUUM_NEXUS_OPT_LEVEL", "7", "must be between 0 and 2"),
        ],
    )
    def test_submit_rejects_malformed_env_config(self, env, value, match):
        """Misconfiguration fails loudly and names the variable.

        Left unvalidated, ``COMPILE_TIMEOUT=0`` makes every submit report "did
        not complete within 0 seconds", which reads like a NEXUS outage rather
        than a config error.
        """
        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        device = _make_device()
        with (
            patch.dict(os.environ, {env: value}),
            pytest.raises(QuantinuumDeviceError, match=match),
        ):
            device.submit(Circuit(2), shots=100)


# --- Transport hardening ---


class TestTransportHardening:
    def test_retry_transient_rejects_zero_attempts(self):
        """``attempts=0`` would skip the loop and raise a bare ``AssertionError``."""
        with pytest.raises(ValueError, match="at least 1"):
            retry_transient(lambda: None, attempts=0)

    @patch("qbraid.runtime.quantinuum._transport.time.sleep")
    def test_retry_transient_gives_up_after_attempts(self, _mock_sleep):
        """Retries are bounded; the last failure propagates."""
        # pylint: disable-next=import-outside-toplevel
        import httpx

        calls = []

        def _always_fails():
            calls.append(1)
            raise httpx.ConnectError("connection refused")

        with pytest.raises(httpx.ConnectError):
            retry_transient(_always_fails, attempts=3)
        assert len(calls) == 3

    def test_ensure_bounded_client_bounds_an_unbounded_client(self):
        """qnexus builds its shared client with ``timeout=None``."""
        # pylint: disable-next=import-outside-toplevel
        import httpx

        client = httpx.Client(timeout=None)
        with patch("qnexus.client.get_nexus_client", return_value=client):
            ensure_bounded_client()

        assert client.timeout.read == DEFAULT_HTTP_TIMEOUT_SECONDS
        assert client.timeout.connect == DEFAULT_HTTP_TIMEOUT_SECONDS

    def test_ensure_bounded_client_preserves_caller_configuration(self):
        """A client that already has a timeout keeps it."""
        # pylint: disable-next=import-outside-toplevel
        import httpx

        client = httpx.Client(timeout=5.0)
        with patch("qnexus.client.get_nexus_client", return_value=client):
            ensure_bounded_client()

        assert client.timeout.read == 5.0

    @patch.dict(os.environ, {"QUANTINUUM_NEXUS_HTTP_TIMEOUT": "12.5"})
    def test_ensure_bounded_client_env_override_wins(self):
        """An explicit env override applies even to an already-bounded client."""
        # pylint: disable-next=import-outside-toplevel
        import httpx

        client = httpx.Client(timeout=5.0)
        with patch("qnexus.client.get_nexus_client", return_value=client):
            ensure_bounded_client()

        assert client.timeout.read == 12.5

    def test_ensure_bounded_client_fills_partial_timeout(self):
        """A partially configured timeout gets its ``None`` holes filled.

        ``httpx.Timeout(5.0, read=None)`` is constructible, and treating it as
        "caller configured, keep it" would leave a hung read able to pin the
        thread — the exact failure this module exists to prevent. Configured
        components must survive; only the holes get the default.
        """
        # pylint: disable-next=import-outside-toplevel
        import httpx

        client = httpx.Client(timeout=httpx.Timeout(5.0, read=None))
        with patch("qnexus.client.get_nexus_client", return_value=client):
            ensure_bounded_client()

        assert client.timeout.read == DEFAULT_HTTP_TIMEOUT_SECONDS
        assert client.timeout.connect == 5.0
        assert client.timeout.write == 5.0
        assert client.timeout.pool == 5.0

    @patch("qbraid.runtime.quantinuum._transport.time.sleep")
    def test_retry_transient_rejects_statusless_resource_errors(self, _mock_sleep):
        """A qnexus resource error with no status code is semantic, not transient.

        qnexus raises ``ResourceFetchFailed(message="Job status: ...")`` with
        ``status_code=None`` when a job finishes in a non-COMPLETED state.
        Repeating the call cannot change that outcome, so it must surface on
        the first attempt rather than after three misleading "transient" logs.
        """
        # pylint: disable-next=import-outside-toplevel
        import qnexus.exceptions as qnx_exc

        calls = []

        def _semantic_failure():
            calls.append(1)
            raise qnx_exc.ResourceFetchFailed(message="Job status: ERROR")

        with pytest.raises(qnx_exc.ResourceFetchFailed):
            retry_transient(_semantic_failure, attempts=3)
        assert len(calls) == 1


# --- Job ---


def _nexus_status(name: str, **kwargs):
    """Build a real qnexus ``JobStatus`` for the given status name."""
    # pylint: disable=import-outside-toplevel
    from qnexus.models.job_status import JobStatus as NexusJobStatus
    from qnexus.models.job_status import JobStatusEnum

    # pylint: enable=import-outside-toplevel

    return NexusJobStatus(status=JobStatusEnum(name), **kwargs)


class TestQuantinuumJob:
    @pytest.mark.parametrize(
        ("nexus_status", "expected"),
        [
            ("COMPLETED", JobStatus.COMPLETED),
            ("RUNNING", JobStatus.RUNNING),
            ("QUEUED", JobStatus.QUEUED),
            ("SUBMITTED", JobStatus.QUEUED),
            ("CANCELLING", JobStatus.CANCELLING),
            ("TERMINATED", JobStatus.FAILED),
            ("DEPLETED", JobStatus.FAILED),
        ],
    )
    @patch("qnexus.jobs.status")
    def test_status(self, mock_status, nexus_status, expected):
        mock_status.return_value = _nexus_status(nexus_status)
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        assert job.status() == expected

    @patch("qnexus.jobs.status")
    def test_status_queries_nexus_rather_than_the_ref_snapshot(self, mock_status):
        """``status`` must re-query NEXUS on every non-terminal call.

        ``JobRef.last_status`` is a plain field fixed when the reference was
        built, so a job held across a run -- the ordinary
        ``job = device.run(...)`` case -- would report its submission-time
        status forever and never observe completion. Here the ref claims
        ``SUBMITTED`` throughout while NEXUS progresses to ``COMPLETED``.
        """
        stale_ref = MagicMock(name="ref")
        stale_ref.last_status = "SUBMITTED"
        mock_status.side_effect = [
            _nexus_status("SUBMITTED"),
            _nexus_status("RUNNING"),
            _nexus_status("COMPLETED"),
        ]

        job = QuantinuumJob(job_id="job-123", job=stale_ref)
        assert job.status() == JobStatus.QUEUED
        assert job.status() == JobStatus.RUNNING
        assert job.status() == JobStatus.COMPLETED
        assert mock_status.call_count == 3

    @patch("qnexus.jobs.status")
    def test_status_failed_logs_message(self, mock_status, caplog):
        mock_status.return_value = _nexus_status(
            "ERROR", message="job errored", error_detail="compilation failed"
        )
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        with caplog.at_level("ERROR"):
            assert job.status() == JobStatus.FAILED
        assert "compilation failed" in caplog.text

    @patch("qnexus.jobs.status")
    def test_status_caches_terminal(self, mock_status):
        """Once terminal, the status is cached and NEXUS is not queried again."""
        mock_status.return_value = _nexus_status("COMPLETED")
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        assert job.status() == JobStatus.COMPLETED
        assert job.status() == JobStatus.COMPLETED
        mock_status.assert_called_once()

    @patch("qnexus.jobs.status")
    def test_status_unknown_on_unrecognized_value(self, mock_status):
        """An unrecognized status maps to UNKNOWN rather than raising."""
        mock_status.return_value = SimpleNamespace(
            status=SimpleNamespace(value="SOMETHING_UNEXPECTED"),
            message="",
            error_detail=None,
        )
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        assert job.status() == JobStatus.UNKNOWN

    @patch("qnexus.jobs.status")
    def test_status_wraps_lookup_errors(self, mock_status):
        """Failures fetching the status are wrapped as QuantinuumJobError."""
        mock_status.side_effect = RuntimeError("connection lost")
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
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

    @patch("qnexus.jobs.status")
    def test_execution_time_not_completed(self, mock_status):
        mock_status.return_value = _nexus_status("RUNNING")
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        assert job.execution_time_s() is None

    @patch("qnexus.jobs.status")
    def test_execution_time_computes_delta(self, mock_status):
        start = datetime.now(timezone.utc)
        end = start + timedelta(seconds=42)
        mock_status.return_value = _nexus_status(
            "COMPLETED", running_time=start, completed_time=end
        )
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        assert job.execution_time_s() == pytest.approx(42.0)

    @patch("qnexus.jobs.status")
    def test_execution_time_missing_timestamps_raises(self, mock_status):
        mock_status.return_value = _nexus_status("COMPLETED")
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        with pytest.raises(QuantinuumJobError, match="completed_time or running_time is missing"):
            job.execution_time_s()

    def test_execution_time_missing_detail_raises(self):
        """A job whose terminal status came from cached metadata has no detail."""
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        job._cache_metadata["status"] = JobStatus.COMPLETED  # pylint: disable=protected-access
        with pytest.raises(QuantinuumJobError, match="status detail is missing"):
            job.execution_time_s()

    @patch("qnexus.jobs.status")
    def test_result_failed_job_raises(self, mock_status):
        mock_status.return_value = _nexus_status("ERROR", error_detail="segfault")
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        with pytest.raises(QuantinuumJobError, match="segfault"):
            job.result()

    @patch("qnexus.jobs.status")
    @patch("qnexus.jobs.results")
    def test_result_single_circuit(self, mock_results, mock_status):
        # pylint: disable-next=import-outside-toplevel
        from pytket.circuit import BasisOrder

        # Asymmetric keys: a palindromic fixture such as {"00", "11"} would
        # look identical under a bit-order flip and prove nothing about the
        # dlo conversion.
        download = MagicMock()
        download.get_counts.return_value = {(0, 0, 1): 512, (0, 1, 1): 488}
        result_item = MagicMock()
        result_item.download_result.return_value = download
        mock_results.return_value = [result_item]
        mock_status.return_value = _nexus_status("COMPLETED")

        mock_device = MagicMock()
        mock_device.id = "H1-1E"

        job = QuantinuumJob(job_id="job-123", device=mock_device, job=MagicMock(name="ref"))
        result = job.result()

        assert result.success is True
        assert result.data.measurement_counts == {"001": 512, "011": 488}
        download.get_counts.assert_called_once_with(basis=BasisOrder.dlo)

    @patch("qnexus.jobs.status")
    @patch("qnexus.jobs.results")
    def test_result_batch(self, mock_results, mock_status):
        def make_item(counts):
            download = MagicMock()
            download.get_counts.return_value = counts
            item = MagicMock()
            item.download_result.return_value = download
            return item

        mock_results.return_value = [
            make_item({(0, 0, 1): 100}),
            make_item({(0, 1, 1): 100}),
        ]
        mock_status.return_value = _nexus_status("COMPLETED")

        mock_device = MagicMock()
        mock_device.id = "H1-1E"

        job = QuantinuumJob(job_id="job-123", device=mock_device, job=MagicMock(name="ref"))
        result = job.result()

        assert result.data.measurement_counts == [{"001": 100}, {"011": 100}]

    @patch("qnexus.jobs.status")
    @patch("qnexus.jobs.results")
    def test_result_empty_raises(self, mock_results, mock_status):
        mock_results.return_value = []
        mock_status.return_value = _nexus_status("COMPLETED")
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        with pytest.raises(QuantinuumJobError, match="No results available"):
            job.result()

    @patch("qnexus.jobs.status")
    @patch("qnexus.jobs.results")
    def test_result_wraps_remote_errors(self, mock_results, mock_status):
        """Errors from ``qnx.jobs.results`` should surface as QuantinuumJobError."""
        mock_results.side_effect = RuntimeError("nexus timeout")
        mock_status.return_value = _nexus_status("COMPLETED")
        job = QuantinuumJob(job_id="job-123", job=MagicMock(name="ref"))
        with pytest.raises(QuantinuumJobError, match="Failed to fetch results"):
            job.result()

    @patch("qnexus.jobs.status")
    @patch("qnexus.jobs.results")
    def test_result_derives_device_id_from_job_metadata(self, mock_results, mock_status):
        """When no device is attached, prefer the device_name recorded on the job ref."""
        # pylint: disable-next=import-outside-toplevel
        from quantinuum_schemas.models.backend_config import QuantinuumConfig

        download = MagicMock()
        download.get_counts.return_value = {(0, 0): 10}
        result_item = MagicMock()
        result_item.download_result.return_value = download
        mock_results.return_value = [result_item]
        mock_status.return_value = _nexus_status("COMPLETED")

        mock_ref = SimpleNamespace(backend_config=QuantinuumConfig(device_name="H2-1"))
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        result = job.result()
        assert result.device_id == "H2-1"

    @patch("qnexus.jobs.status")
    @patch("qnexus.jobs.results")
    def test_result_falls_back_to_generic_device_id(self, mock_results, mock_status):
        """Fallback label when backend_config is not a QuantinuumConfig."""
        # pylint: disable-next=import-outside-toplevel
        from quantinuum_schemas.models.backend_config import AerConfig

        download = MagicMock()
        download.get_counts.return_value = {(0, 0): 10}
        result_item = MagicMock()
        result_item.download_result.return_value = download
        mock_results.return_value = [result_item]
        mock_status.return_value = _nexus_status("COMPLETED")

        mock_ref = SimpleNamespace(backend_config=AerConfig())
        job = QuantinuumJob(job_id="job-123", job=mock_ref)
        result = job.result()
        assert result.device_id == "quantinuum"


# Silence unused-import warnings from conditional imports referenced only in tests.
_ = QuantinuumDeviceError

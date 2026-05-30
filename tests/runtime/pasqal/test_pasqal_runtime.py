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
"""Unit tests for Pasqal provider, device, and job classes."""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("pasqal_cloud")
pytest.importorskip("pulser")

# pylint: disable=wrong-import-position
from pulser import Register, Sequence  # noqa: E402
from pulser.devices import AnalogDevice  # noqa: E402

from qbraid.programs import ExperimentType  # noqa: E402
from qbraid.runtime.enums import DeviceStatus, JobStatus  # noqa: E402
from qbraid.runtime.exceptions import ResourceNotFoundError  # noqa: E402
from qbraid.runtime.pasqal import PasqalDevice, PasqalJob, PasqalProvider  # noqa: E402
from qbraid.runtime.pasqal.device import PasqalDeviceError  # noqa: E402
from qbraid.runtime.pasqal.job import (  # noqa: E402
    _PASQAL_STATUS_MAP,
    PasqalJobError,
    _map_pasqal_status,
)
from qbraid.runtime.pasqal.provider import _build_profile, _is_simulator  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_sdk():
    sdk = MagicMock(name="PasqalSDK")
    sdk.project_id = "proj-1"
    sdk.get_device_specs_dict.return_value = {
        "FRESNEL": '{"max_atom_num": 100}',
        "EMU_FREE": '{"max_atom_num": 10}',
        "EMU_TN": '{"max_atom_num": 20}',
    }
    return sdk


def _make_pulser_sequence():

    reg = Register({"q0": (0.0, 0.0)})
    return Sequence(reg, AnalogDevice)


def _make_job(status: str = "DONE", counter: dict[str, int] | None = None, job_id: str = "job-1"):
    counter = {"00": 50, "11": 50} if counter is None else counter
    job = MagicMock(name=f"PasqalJob[{job_id}]")
    job.id = job_id
    job.status = status
    job.result = counter
    job.full_result = {"counter": counter}
    return job


def _make_batch(
    batch_id: str = "batch-1",
    status: str = "DONE",
    jobs: list[Any] | None = None,
    errors: list | None = None,
):
    jobs = jobs if jobs is not None else [_make_job()]
    batch = MagicMock(name=f"PasqalBatch[{batch_id}]")
    batch.id = batch_id
    batch.status = status
    batch.ordered_jobs = jobs
    batch.errors = errors
    return batch


# ---------------------------------------------------------------------------
# Status mapping
# ---------------------------------------------------------------------------


class TestStatusMapping:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("PENDING", JobStatus.QUEUED),
            ("RUNNING", JobStatus.RUNNING),
            ("DONE", JobStatus.COMPLETED),
            ("ERROR", JobStatus.FAILED),
            ("CANCELED", JobStatus.CANCELLED),
            ("TIMED_OUT", JobStatus.FAILED),
            ("PAUSED", JobStatus.QUEUED),
            ("done", JobStatus.COMPLETED),  # case-insensitive
            ("SOMETHING_NEW", JobStatus.UNKNOWN),
            (None, JobStatus.UNKNOWN),
        ],
    )
    def test_map_pasqal_status(self, raw, expected):
        assert _map_pasqal_status(raw) == expected

    def test_status_map_covers_expected_states(self):
        expected = {"PENDING", "RUNNING", "DONE", "ERROR", "CANCELED", "TIMED_OUT", "PAUSED"}
        assert set(_PASQAL_STATUS_MAP.keys()) == expected


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class TestProviderHelpers:
    @pytest.mark.parametrize(
        ("device_id", "is_sim"),
        [
            ("FRESNEL", False),
            ("FRESNEL_CAN1", False),
            ("EMU_FREE", True),
            ("EMU_TN", True),
            ("emu_sv", True),
        ],
    )
    def test_is_simulator(self, device_id, is_sim):
        assert _is_simulator(device_id) is is_sim

    def test_build_profile_basic(self):
        profile = _build_profile("EMU_FREE", num_qubits=10)
        assert profile.device_id == "EMU_FREE"
        assert profile.simulator is True
        assert profile.experiment_type == ExperimentType.ANALOG
        assert profile.num_qubits == 10
        assert profile.provider_name == "pasqal"
        assert profile.program_spec.alias == "pulser"

    def test_build_profile_qpu(self):
        profile = _build_profile("FRESNEL")
        assert profile.simulator is False
        assert profile.num_qubits is None

    def test_program_spec_serializer_uses_abstract_repr(self):
        profile = _build_profile("EMU_FREE")
        seq = _make_pulser_sequence()
        serialized = profile.program_spec.serialize(seq)
        assert isinstance(serialized, str)
        data = json.loads(serialized)
        assert "register" in data


class TestPasqalProvider:
    def test_init_requires_credentials(self, monkeypatch):
        for key in ("PASQAL_USERNAME", "PASQAL_PASSWORD", "PASQAL_PROJECT_ID"):
            monkeypatch.delenv(key, raising=False)
        with pytest.raises(ValueError, match="Pasqal authentication is required"):
            PasqalProvider()

    def test_init_with_sdk_short_circuits(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        assert provider.sdk is mock_sdk

    def test_init_with_username_password(self):
        # Patch the SDK constructor used inside the provider.
        sdk_mock = MagicMock(name="PasqalSDK")
        with patch("pasqal_cloud.SDK", return_value=sdk_mock) as ctor:
            provider = PasqalProvider(
                username="me@example.com",
                password="hunter2",
                project_id="proj-9",
            )
        ctor.assert_called_once()
        kwargs = ctor.call_args.kwargs
        assert kwargs["username"] == "me@example.com"
        assert kwargs["password"] == "hunter2"
        assert kwargs["project_id"] == "proj-9"
        assert kwargs["token_provider"] is None
        assert provider.sdk is sdk_mock

    def test_init_uses_env_vars(self, monkeypatch):
        monkeypatch.setenv("PASQAL_USERNAME", "env@example.com")
        monkeypatch.setenv("PASQAL_PASSWORD", "envpass")
        monkeypatch.setenv("PASQAL_PROJECT_ID", "env-proj")
        sdk_mock = MagicMock(name="PasqalSDK")
        with patch("pasqal_cloud.SDK", return_value=sdk_mock) as ctor:
            PasqalProvider()
        kwargs = ctor.call_args.kwargs
        assert kwargs["username"] == "env@example.com"
        assert kwargs["password"] == "envpass"
        assert kwargs["project_id"] == "env-proj"

    def test_init_with_token_provider(self):
        token_provider = MagicMock(name="TokenProvider")
        sdk_mock = MagicMock(name="PasqalSDK")
        with patch("pasqal_cloud.SDK", return_value=sdk_mock) as ctor:
            PasqalProvider(token_provider=token_provider, project_id="proj-1")
        kwargs = ctor.call_args.kwargs
        assert kwargs["token_provider"] is token_provider
        assert kwargs["username"] is None

    def test_get_devices_uses_spec_keys(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        devices = provider.get_devices()
        expected = {
            "FRESNEL",
            "FRESNEL_CAN1",
            "EMU_FREE",
            "EMU_TN",
            "EMU_FRESNEL",
            "EMU_MPS",
            "EMU_SV",
        }
        assert {d.id for d in devices} == expected
        for device in devices:
            assert isinstance(device, PasqalDevice)
            assert device.profile.experiment_type == ExperimentType.ANALOG

    def test_get_devices_fallback_when_specs_unavailable(self, mock_sdk):
        mock_sdk.get_device_specs_dict.side_effect = RuntimeError("network down")
        provider = PasqalProvider(sdk=mock_sdk)
        devices = provider.get_devices()
        expected = {
            "FRESNEL",
            "FRESNEL_CAN1",
            "EMU_FREE",
            "EMU_TN",
            "EMU_FRESNEL",
            "EMU_MPS",
            "EMU_SV",
        }
        assert {d.id for d in devices} == expected

    def test_get_device_known(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("emu_free")  # case-insensitive
        assert isinstance(device, PasqalDevice)
        assert device.id == "EMU_FREE"
        assert device.profile.simulator is True

    def test_get_device_unknown(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        with pytest.raises(ResourceNotFoundError, match="Device 'NOT_REAL' not found"):
            provider.get_device("NOT_REAL")

    def test_hashable(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        # Hash must not raise and must be stable for the same instance.
        assert hash(provider) == hash(provider)


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------


class TestPasqalDevice:
    def test_status_is_online(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_FREE")
        assert device.status() == DeviceStatus.ONLINE

    def test_str(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_FREE")
        assert str(device) == "PasqalDevice('EMU_FREE')"

    def test_submit_single_sequence(self, mock_sdk):
        batch = _make_batch(batch_id="batch-xyz")
        mock_sdk.create_batch.return_value = batch

        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_FREE")
        sequence = '{"foo": 1}'

        job = device.submit(sequence, shots=200)

        assert isinstance(job, PasqalJob)
        assert job.id == "batch-xyz"
        mock_sdk.create_batch.assert_called_once()
        call_kwargs = mock_sdk.create_batch.call_args.kwargs
        assert call_kwargs["wait"] is False
        assert call_kwargs["jobs"] == [{"runs": 200, "serialized_sequence": '{"foo": 1}'}]
        # Device type must be the enum member for "EMU_FREE".
        assert str(call_kwargs["device_type"]) == "EMU_FREE"

    def test_submit_list_of_sequences(self, mock_sdk):
        batch = _make_batch(batch_id="batch-multi")
        mock_sdk.create_batch.return_value = batch

        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_TN")
        sequences = ['{"i": 0}', '{"i": 1}']

        job = device.submit(sequences, shots=50)
        assert job.id == "batch-multi"
        jobs_payload = mock_sdk.create_batch.call_args.kwargs["jobs"]
        assert jobs_payload == [
            {"runs": 50, "serialized_sequence": '{"i": 0}'},
            {"runs": 50, "serialized_sequence": '{"i": 1}'},
        ]

    def test_submit_accepts_pre_serialized_string(self, mock_sdk):
        mock_sdk.create_batch.return_value = _make_batch()
        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_FREE")

        device.submit('{"already": "serialized"}', shots=10)
        payload = mock_sdk.create_batch.call_args.kwargs["jobs"][0]
        assert payload["serialized_sequence"] == '{"already": "serialized"}'

    def test_submit_empty_input_raises(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_FREE")
        with pytest.raises(PasqalDeviceError, match="at least one"):
            device.submit([])

    def test_submit_wraps_sdk_errors(self, mock_sdk):
        mock_sdk.create_batch.side_effect = RuntimeError("api down")
        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_FREE")
        with pytest.raises(PasqalDeviceError, match="Failed to submit batch"):
            device.submit('{"stub": true}')

    def test_submit_invalid_shots_raises(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_FREE")
        with pytest.raises(PasqalDeviceError, match="`shots` must be a positive integer"):
            device.submit('{"stub": true}', shots=0)


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------


class TestPasqalJob:
    def test_init_requires_sdk_or_device(self):
        with pytest.raises(PasqalJobError, match="requires either"):
            PasqalJob(job_id="x")

    def test_init_takes_sdk_from_device(self, mock_sdk):
        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_FREE")
        job = PasqalJob(job_id="batch-1", device=device)
        assert job.sdk is mock_sdk

    def test_status_polls_batch(self, mock_sdk):
        mock_sdk.get_batch.return_value = _make_batch(status="RUNNING")
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        assert job.status() == JobStatus.RUNNING

    def test_status_uses_cache_when_terminal(self, mock_sdk):
        mock_sdk.get_batch.return_value = _make_batch(status="DONE")
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        assert job.status() == JobStatus.COMPLETED
        # Mutate the remote state -- the job should still report COMPLETED.
        mock_sdk.get_batch.return_value = _make_batch(status="ERROR")
        assert job.status() == JobStatus.COMPLETED

    def test_status_wraps_transport_errors(self, mock_sdk):
        mock_sdk.get_batch.side_effect = RuntimeError("oops")
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        with pytest.raises(PasqalJobError, match="Unable to retrieve"):
            job.status()

    def test_cancel(self, mock_sdk):
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        job.cancel()
        mock_sdk.cancel_batch.assert_called_once_with("batch-1")

    def test_cancel_wraps_errors(self, mock_sdk):
        mock_sdk.cancel_batch.side_effect = RuntimeError("nope")
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        with pytest.raises(PasqalJobError, match="Failed to cancel"):
            job.cancel()

    def test_result_single_job(self, mock_sdk):
        counts = {"00": 600, "11": 400}
        mock_sdk.get_batch.return_value = _make_batch(jobs=[_make_job(counter=counts)])
        provider = PasqalProvider(sdk=mock_sdk)
        device = provider.get_device("EMU_FREE")

        job = PasqalJob(job_id="batch-1", sdk=mock_sdk, device=device)
        result = job.result()
        assert result.success is True
        assert result.device_id == "EMU_FREE"
        assert result.job_id == "batch-1"
        assert result.data.get_counts() == counts

    def test_result_multi_job_returns_list(self, mock_sdk):
        counts_a = {"00": 100}
        counts_b = {"01": 100}
        mock_sdk.get_batch.return_value = _make_batch(
            jobs=[
                _make_job(counter=counts_a, job_id="j1"),
                _make_job(counter=counts_b, job_id="j2"),
            ]
        )
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        result = job.result()
        assert result.data.get_counts() == [counts_a, counts_b]

    def test_result_uses_full_result_fallback(self, mock_sdk):
        job_record = MagicMock()
        job_record.id = "j1"
        job_record.result = None  # primary slot empty
        job_record.full_result = {"counter": {"10": 7}}
        mock_sdk.get_batch.return_value = _make_batch(jobs=[job_record])
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        assert job.result().data.get_counts() == {"10": 7}

    def test_result_raises_on_failure(self, mock_sdk):
        mock_sdk.get_batch.return_value = _make_batch(status="ERROR", errors=["bad"])
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        with pytest.raises(PasqalJobError, match="did not complete"):
            job.result()

    def test_result_raises_when_no_jobs(self, mock_sdk):
        mock_sdk.get_batch.return_value = _make_batch(jobs=[])
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        with pytest.raises(PasqalJobError, match="No jobs"):
            job.result()

    def test_result_raises_when_no_counter(self, mock_sdk):
        job_record = MagicMock()
        job_record.id = "j-empty"
        job_record.result = None
        job_record.full_result = {}  # no counter key
        mock_sdk.get_batch.return_value = _make_batch(jobs=[job_record])
        job = PasqalJob(job_id="batch-1", sdk=mock_sdk)
        with pytest.raises(PasqalJobError, match="no counter result"):
            job.result()

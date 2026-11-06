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

import copy
import importlib.util
import json
import sys
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
import requests

pytest.importorskip("pasqal_cloud")
pytest.importorskip("pulser")

# pylint: disable=wrong-import-position
from pasqal_cloud import errors as pasqal_errors  # noqa: E402
from pasqal_cloud.utils.constants import BatchStatus  # noqa: E402
from pulser import Register, Sequence  # noqa: E402
from pulser.devices import AnalogDevice  # noqa: E402

from qbraid.programs import ExperimentType  # noqa: E402
from qbraid.runtime.enums import DeviceStatus, JobStatus  # noqa: E402
from qbraid.runtime.exceptions import ResourceNotFoundError  # noqa: E402
from qbraid.runtime.pasqal import PasqalDevice, PasqalJob, PasqalProvider  # noqa: E402
from qbraid.runtime.pasqal.device import PasqalDeviceError  # noqa: E402
from qbraid.runtime.pasqal.job import (  # noqa: E402
    PasqalJobError,
    _map_pasqal_status,
    _pasqal_cloud_errors,
    _status_map,
)
from qbraid.runtime.pasqal.provider import (  # noqa: E402
    PasqalProviderError,
    PasqalSession,
    _build_profile,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

# Records as returned by Pasqal's GET /api/v1/devices (trimmed to the fields
# qBraid reads). FRESNEL is deliberately absent: Pasqal drops a QPU from the
# catalog while it is in maintenance.
CATALOG: dict[str, dict[str, Any]] = {
    "FRESNEL_CAN1": {
        "device_type": "FRESNEL_CAN1",
        "status": "UP",
        "active": True,
        "availability": "ACTIVE",
        "average_queue_time": 0,
        "max_atom_num": 100,
        "is_emulator": False,
    },
    "EMU_MPS": {
        "device_type": "EMU_MPS",
        "status": "UP",
        "active": True,
        "availability": "ACTIVE",
        "average_queue_time": 2,
        "max_atom_num": 80,
        "is_emulator": True,
    },
    "EMU_FREE": {
        "device_type": "EMU_FREE",
        "status": "UP",
        "active": True,
        "availability": "ACTIVE",
        "average_queue_time": 1,
        "max_atom_num": 12,
        "is_emulator": True,
    },
    "EMU_TN": {
        "device_type": "EMU_TN",
        "status": "UP",
        "active": True,
        "availability": "ACTIVE",
        "average_queue_time": 0,
        "max_atom_num": 100,
        "is_emulator": True,
    },
    "EMU_FRESNEL": {
        "device_type": "EMU_FRESNEL",
        "status": "UP",
        "active": True,
        "availability": "ACTIVE",
        "average_queue_time": 0,
        "max_atom_num": 100,
        "is_emulator": True,
    },
    "EMU_SV": {
        "device_type": "EMU_SV",
        "status": "UP",
        "active": True,
        "availability": "ACTIVE",
        "average_queue_time": 2,
        "max_atom_num": 25,
        "is_emulator": True,
    },
}

# The class PasqalProvider builds: pasqal-cloud 0.21-0.22, which the extra allows, have only SDK.
_HAS_CLIENT = importlib.util.find_spec("pasqal_cloud.pasqal_cloud_client") is not None
CLIENT_CLASS = f"pasqal_cloud.{'pasqal_cloud_client.PasqalCloudClient' if _HAS_CLIENT else 'SDK'}"

ALL_DEVICE_TYPES = {
    "FRESNEL",
    "FRESNEL_CAN1",
    "EMU_FREE",
    "EMU_TN",
    "EMU_FRESNEL",
    "EMU_MPS",
    "EMU_SV",
}


@pytest.fixture
def catalog(monkeypatch):
    """Serve a mutable copy of :data:`CATALOG` in place of the live device catalog."""
    records = copy.deepcopy(CATALOG)
    monkeypatch.setattr(PasqalSession, "get_device_records", lambda self: records)
    return records


@pytest.fixture
def mock_client(catalog):  # pylint: disable=unused-argument
    """Return a stand-in ``pasqal_cloud`` client pointed at the production core URL."""
    client = MagicMock(name="PasqalCloudClient")
    client.project_id = "proj-1"
    client._client.endpoints.core = "https://apis.pasqal.cloud/core-fast"
    return client


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


def _make_batch(  # pylint: disable=too-many-arguments
    batch_id: str = "batch-1",
    status: str = "DONE",
    jobs: list[Any] | None = None,
    errors: list | None = None,
    started: str | None = "2026-11-05T21:48:15.500000+00:00",
    ended: str | None = "2026-11-05T21:48:17.750000+00:00",
):
    jobs = jobs if jobs is not None else [_make_job()]
    batch = MagicMock(name=f"PasqalBatch[{batch_id}]")
    batch.id = batch_id
    batch.status = status
    batch.ordered_jobs = jobs
    batch.errors = errors
    batch.created_at = "2026-11-05T21:48:13.648700+00:00"
    batch.start_datetime = started
    batch.end_datetime = ended
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
        ],
    )
    def test_map_pasqal_status(self, raw, expected):
        """Each Pasqal batch status maps to the matching qBraid status."""
        assert _map_pasqal_status(raw) == expected

    def test_paused_maps_to_queued(self):
        """PAUSED, documented by Pasqal but absent from BatchStatus, reads as queued."""
        assert _map_pasqal_status("PAUSED") == JobStatus.QUEUED

    @pytest.mark.parametrize("raw", ["SOMETHING_NEW", "done"])
    def test_unrecognized_status_raises(self, raw):
        """An unknown status raises rather than returning non-terminal UNKNOWN."""
        with pytest.raises(PasqalJobError, match="Unrecognized Pasqal batch status"):
            _map_pasqal_status(raw)

    def test_status_map_is_exhaustive(self):
        """Every pasqal-cloud BatchStatus member is mapped."""
        assert set(_status_map()) == set(BatchStatus)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class TestProviderHelpers:
    def test_build_profile_from_catalog_record(self):
        """A listed device takes its atom count and emulator flag from the catalog."""
        profile = _build_profile("EMU_MPS", CATALOG["EMU_MPS"])
        assert profile.device_id == "EMU_MPS"
        assert profile.simulator is True
        assert profile.experiment_type == ExperimentType.ANALOG
        assert profile.num_qubits == 80
        assert profile.provider_name == "pasqal"
        assert profile.program_spec.alias == "pulser"

    def test_build_profile_qpu_from_catalog_record(self):
        """A listed QPU is not a simulator and carries its atom count."""
        profile = _build_profile("FRESNEL_CAN1", CATALOG["FRESNEL_CAN1"])
        assert profile.simulator is False
        assert profile.num_qubits == 100

    def test_build_profile_unlisted_device(self):
        """An unlisted device has no atom count; the EMU_ prefix decides simulator."""
        assert _build_profile("FRESNEL").simulator is False
        assert _build_profile("FRESNEL").num_qubits is None
        assert _build_profile("EMU_FREE").simulator is True

    def test_program_spec_serializer_uses_abstract_repr(self):
        """The program spec serializes a Pulser Sequence to its abstract repr."""
        profile = _build_profile("EMU_FREE")
        seq = _make_pulser_sequence()
        serialized = profile.program_spec.serialize(seq)
        assert isinstance(serialized, str)
        data = json.loads(serialized)
        assert "register" in data


class TestPasqalSession:
    def _response(self, payload: Any, status_code: int = 200) -> MagicMock:
        response = MagicMock(name="Response")
        response.status_code = status_code
        response.json.return_value = payload
        if status_code >= 400:
            response.raise_for_status.side_effect = RuntimeError(f"HTTP {status_code}")
        return response

    def test_get_device_records_keys_by_device_type(self):
        """Catalog records are keyed by device type."""
        session = PasqalSession("https://apis.pasqal.cloud/core-fast/")
        payload = {"data": list(CATALOG.values())}
        with patch.object(session, "get", return_value=self._response(payload)) as get:
            records = session.get_device_records()
        get.assert_called_once_with(
            "https://apis.pasqal.cloud/core-fast/api/v1/devices", timeout=10.0
        )
        assert records == CATALOG

    def test_get_device_records_skips_records_without_device_type(self):
        """A record without a device_type is dropped, not fatal."""
        session = PasqalSession("https://apis.pasqal.cloud/core-fast")
        payload = {"data": [{"status": "UP"}, CATALOG["EMU_FREE"]]}
        with patch.object(session, "get", return_value=self._response(payload)):
            assert set(session.get_device_records()) == {"EMU_FREE"}

    def test_get_device_records_is_cached_briefly(self):
        """Repeated reads within the TTL make one request; a stale cache refetches."""
        session = PasqalSession("https://apis.pasqal.cloud/core-fast")
        payload = {"data": list(CATALOG.values())}
        with patch.object(session, "get", return_value=self._response(payload)) as get:
            session.get_device_records()
            session.get_device_records()
            assert get.call_count == 1
            session._cached_at -= PasqalSession.CACHE_TTL_SECONDS
            session.get_device_records()
            assert get.call_count == 2

    def test_get_device_records_returns_a_copy(self):
        """Changing a returned catalog, or a record in it, does not change the cache."""
        session = PasqalSession("https://apis.pasqal.cloud/core-fast")
        payload = {"data": copy.deepcopy(list(CATALOG.values()))}
        with patch.object(session, "get", return_value=self._response(payload)):
            session.get_device_records().pop("EMU_FREE")
            session.get_device_records()["EMU_MPS"]["status"] = "DOWN"
            records = session.get_device_records()
        assert "EMU_FREE" in records
        assert records["EMU_MPS"]["status"] == "UP"

    def test_get_device_records_remembers_a_failure_briefly(self):
        """During an outage, callers re-raise the recent failure instead of refetching."""
        session = PasqalSession("https://apis.pasqal.cloud/core-fast")
        with patch.object(session, "get", return_value=self._response({}, 503)) as get:
            raised = []
            for _ in range(3):
                with pytest.raises(PasqalProviderError, match="device catalog") as exc_info:
                    session.get_device_records()
                raised.append(exc_info.value)
            assert get.call_count == 1
            # Each caller gets its own error, so tracebacks do not pile up on one object.
            assert len({id(err) for err in raised}) == 3
            session._failed_at -= PasqalSession.FAILURE_TTL_SECONDS
            with pytest.raises(PasqalProviderError):
                session.get_device_records()
            assert get.call_count == 2

    def test_get_device_records_http_error(self):
        """An HTTP failure raises PasqalProviderError."""
        session = PasqalSession("https://apis.pasqal.cloud/core-fast")
        with patch.object(session, "get", return_value=self._response({}, status_code=503)):
            with pytest.raises(PasqalProviderError, match="device catalog"):
                session.get_device_records()

    @pytest.mark.parametrize(
        "payload", [{"unexpected": []}, {"data": {"EMU_FREE": {}}}, {"data": "EMU_FREE"}]
    )
    def test_get_device_records_malformed_payload(self, payload):
        """A payload without a list of records in ``data`` raises, not an empty catalog."""
        session = PasqalSession("https://apis.pasqal.cloud/core-fast")
        with patch.object(session, "get", return_value=self._response(payload)):
            with pytest.raises(PasqalProviderError, match="device catalog"):
                session.get_device_records()


class TestPasqalProvider:
    @pytest.fixture(autouse=True)
    def _clear_pasqal_env(self, monkeypatch):
        # CI exports PASQAL_* from repository secrets, so credentials resolved from the
        # environment would otherwise leak into every constructor assertion below.
        for key in ("PASQAL_USERNAME", "PASQAL_PASSWORD", "PASQAL_PROJECT_ID"):
            monkeypatch.delenv(key, raising=False)

    def test_init_requires_credentials(self):
        """Constructing without any credential raises."""
        with pytest.raises(ValueError, match="Pasqal authentication is required"):
            PasqalProvider()

    def test_init_with_sdk_short_circuits(self, mock_client):
        """A pre-built client is used as is."""
        provider = PasqalProvider(client=mock_client)
        assert provider.client is mock_client

    def test_session_targets_client_core_url(self, mock_client):
        """The catalog session uses the same core URL (region) as the client."""
        mock_client._client.endpoints.core = "https://apis.sa.pasqal.cloud/core-fast"
        provider = PasqalProvider(client=mock_client)
        assert provider.session.base_url == "https://apis.sa.pasqal.cloud/core-fast"

    def test_session_defaults_to_production_core_url(self):
        """A client without endpoints falls back to the production core URL."""
        client = MagicMock(name="PasqalCloudClient", spec=["project_id"])
        provider = PasqalProvider(client=client)
        assert provider.session.base_url == "https://apis.pasqal.cloud/core-fast"

    def test_init_with_username_password(self):
        """Username, password and project are forwarded to PasqalCloudClient."""
        client_mock = MagicMock(name="PasqalCloudClient")
        target = CLIENT_CLASS
        with patch(target, return_value=client_mock) as ctor:
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
        assert provider.client is client_mock

    def test_init_falls_back_to_legacy_sdk(self, monkeypatch):
        """pasqal-cloud releases without PasqalCloudClient use the SDK class."""
        client_mock = MagicMock(name="PasqalSDK")
        with patch("pasqal_cloud.SDK", return_value=client_mock, create=True) as ctor:
            # Block the new module only after patching: on pasqal-cloud 0.24 the
            # deprecated ``SDK`` name is itself resolved lazily from it.
            monkeypatch.setitem(sys.modules, "pasqal_cloud.pasqal_cloud_client", None)
            provider = PasqalProvider(username="me@example.com", project_id="proj-9")
        ctor.assert_called_once()
        assert provider.client is client_mock

    def test_init_uses_env_vars(self, monkeypatch):
        """Credentials fall back to the PASQAL_* environment variables."""
        monkeypatch.setenv("PASQAL_USERNAME", "env@example.com")
        monkeypatch.setenv("PASQAL_PASSWORD", "envpass")
        monkeypatch.setenv("PASQAL_PROJECT_ID", "env-proj")
        client_mock = MagicMock(name="PasqalCloudClient")
        target = CLIENT_CLASS
        with patch(target, return_value=client_mock) as ctor:
            PasqalProvider()
        kwargs = ctor.call_args.kwargs
        assert kwargs["username"] == "env@example.com"
        assert kwargs["password"] == "envpass"
        assert kwargs["project_id"] == "env-proj"

    def test_init_with_token_provider(self):
        """A token provider is forwarded and no username is required."""
        token_provider = MagicMock(name="TokenProvider")
        client_mock = MagicMock(name="PasqalCloudClient")
        target = CLIENT_CLASS
        with patch(target, return_value=client_mock) as ctor:
            PasqalProvider(token_provider=token_provider, project_id="proj-1")
        kwargs = ctor.call_args.kwargs
        assert kwargs["token_provider"] is token_provider
        assert kwargs["username"] is None

    def test_get_devices_lists_every_device_type(self, mock_client):
        """Every DeviceTypeName is listed, including a QPU absent from the catalog."""
        provider = PasqalProvider(client=mock_client)
        devices = provider.get_devices()
        assert {d.id for d in devices} == ALL_DEVICE_TYPES
        by_id = {d.id: d for d in devices}
        assert by_id["EMU_SV"].num_qubits == 25
        assert by_id["FRESNEL"].num_qubits is None
        for device in devices:
            assert isinstance(device, PasqalDevice)
            assert device.profile.experiment_type == ExperimentType.ANALOG

    def test_get_devices_includes_new_catalog_device(self, mock_client, catalog):
        """A device Pasqal lists before pasqal-cloud enumerates it is listed, but unavailable."""
        catalog["EMU_NEW"] = {**CATALOG["EMU_SV"], "device_type": "EMU_NEW"}
        provider = PasqalProvider(client=mock_client)
        devices = {d.id: d for d in provider.get_devices()}
        assert devices["EMU_NEW"].status() == DeviceStatus.UNAVAILABLE

    def test_boolean_atom_count_is_ignored(self, mock_client, catalog):
        """A boolean max_atom_num is not taken as a qubit count."""
        catalog["EMU_SV"]["max_atom_num"] = True
        assert PasqalProvider(client=mock_client).get_device("EMU_SV").num_qubits is None

    def test_get_devices_tolerates_incomplete_records(self, mock_client, catalog):
        """A record without an atom count or emulator flag still yields a device."""
        del catalog["EMU_SV"]["max_atom_num"]
        del catalog["EMU_SV"]["is_emulator"]
        device = PasqalProvider(client=mock_client).get_device("EMU_SV")
        assert device.num_qubits is None
        assert device.simulator is True

    def test_get_devices_raises_when_catalog_unavailable(self, mock_client, monkeypatch):
        """A catalog failure surfaces instead of returning guessed devices."""

        def _fail(_self):
            raise PasqalProviderError("Failed to fetch the Pasqal device catalog: down")

        monkeypatch.setattr(PasqalSession, "get_device_records", _fail)
        provider = PasqalProvider(client=mock_client)
        with pytest.raises(PasqalProviderError, match="device catalog"):
            provider.get_devices()

    def test_get_device_without_catalog_can_still_submit(self, mock_client, monkeypatch):
        """A catalog outage does not block submission, which never reads the catalog.

        Before the fallback, get_device raised here, so a platform submit failed while
        Pasqal itself was accepting batches.
        """

        def _fail(_self):
            raise PasqalProviderError("Failed to fetch the Pasqal device catalog: down")

        monkeypatch.setattr(PasqalSession, "get_device_records", _fail)
        mock_client.create_batch.return_value = _make_batch(batch_id="batch-xyz")
        device = PasqalProvider(client=mock_client).get_device("emu_mps")
        assert device.id == "EMU_MPS"
        assert device.num_qubits is None
        assert device.submit('{"foo": 1}', shots=10).id == "batch-xyz"
        with pytest.raises(PasqalProviderError, match="device catalog"):
            device.status()
        assert device.run(_make_pulser_sequence(), shots=10).id == "batch-xyz"

    def test_get_device_unknown_without_catalog(self, mock_client, monkeypatch):
        """Without the catalog, only device types pasqal-cloud accepts resolve."""

        def _fail(_self):
            raise PasqalProviderError("Failed to fetch the Pasqal device catalog: down")

        monkeypatch.setattr(PasqalSession, "get_device_records", _fail)
        with pytest.raises(ResourceNotFoundError, match="FRESNEL_SA1"):
            PasqalProvider(client=mock_client).get_device("FRESNEL_SA1")

    def test_get_device_known(self, mock_client):
        """Device lookup is case-insensitive and carries catalog limits."""
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("emu_free")  # case-insensitive
        assert isinstance(device, PasqalDevice)
        assert device.id == "EMU_FREE"
        assert device.profile.simulator is True
        assert device.num_qubits == 12

    def test_get_device_unlisted_device_type(self, mock_client):
        """A device type Pasqal accepts but does not list still resolves."""
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("FRESNEL")
        assert device.id == "FRESNEL"
        assert device.num_qubits is None

    def test_get_device_unknown(self, mock_client):
        """An unknown identifier raises ResourceNotFoundError."""
        provider = PasqalProvider(client=mock_client)
        with pytest.raises(ResourceNotFoundError, match="Device 'NOT_REAL' not found"):
            provider.get_device("NOT_REAL")

    def test_hashable(self, mock_client):
        """The provider is hashable and its hash is stable."""
        provider = PasqalProvider(client=mock_client)
        # Hash must not raise and must be stable for the same instance.
        assert hash(provider) == hash(provider)


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------


class TestPasqalDevice:
    def test_status_online_when_up(self, mock_client):
        """A listed, active device reporting UP is ONLINE."""
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_FREE")
        assert device.status() == DeviceStatus.ONLINE

    def test_status_offline_when_unlisted(self, mock_client):
        """A device type missing from the catalog (e.g. in maintenance) is OFFLINE."""
        provider = PasqalProvider(client=mock_client)
        assert provider.get_device("FRESNEL").status() == DeviceStatus.OFFLINE

    def test_status_reads_catalog_live(self, mock_client, catalog):
        """Status reflects the catalog at call time, not at construction."""
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_TN")
        assert device.status() == DeviceStatus.ONLINE
        del catalog["EMU_TN"]
        assert device.status() == DeviceStatus.OFFLINE

    @pytest.mark.parametrize(
        "overrides",
        [
            {"status": "DOWN"},
            {"active": False},
            {"availability": "INACTIVE"},
        ],
    )
    def test_status_unavailable(self, mock_client, catalog, overrides):
        """A listed device that is down, inactive or not ACTIVE is UNAVAILABLE."""
        catalog["EMU_MPS"].update(overrides)
        provider = PasqalProvider(client=mock_client)
        assert provider.get_device("EMU_MPS").status() == DeviceStatus.UNAVAILABLE

    def test_status_unrecognized_value_is_unavailable(self, mock_client, catalog):
        """An unknown status string is UNAVAILABLE, never guessed ONLINE."""
        catalog["EMU_MPS"]["status"] = "CALIBRATING"
        provider = PasqalProvider(client=mock_client)
        with patch("qbraid.runtime.pasqal.device.logger") as log:
            assert provider.get_device("EMU_MPS").status() == DeviceStatus.UNAVAILABLE
        log.warning.assert_called_once()

    def test_status_unavailable_when_record_incomplete(self, mock_client, catalog):
        """A record missing a status field is UNAVAILABLE rather than raising."""
        del catalog["EMU_MPS"]["availability"]
        provider = PasqalProvider(client=mock_client)
        assert provider.get_device("EMU_MPS").status() == DeviceStatus.UNAVAILABLE

    def test_status_unavailable_when_pasqal_cloud_cannot_target(self, mock_client, catalog):
        """A listed device the installed pasqal-cloud cannot submit to is UNAVAILABLE."""
        catalog["FRESNEL_SA1"] = {**CATALOG["FRESNEL_CAN1"], "device_type": "FRESNEL_SA1"}
        device = PasqalProvider(client=mock_client).get_device("FRESNEL_SA1")
        with patch("qbraid.runtime.pasqal.device._WARNED_UNTARGETABLE", set()):
            with patch("qbraid.runtime.pasqal.device.logger") as log:
                assert device.status() == DeviceStatus.UNAVAILABLE
                assert device.status() == DeviceStatus.UNAVAILABLE
        log.warning.assert_called_once()

    def test_metadata_for_unlisted_device(self, mock_client):
        """Metadata works for an unlisted device and omits queue time."""
        metadata = PasqalProvider(client=mock_client).get_device("FRESNEL").metadata()
        assert metadata["status"] == "OFFLINE"
        assert "average_queue_time" not in metadata

    def test_str(self, mock_client):
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_FREE")
        assert str(device) == "PasqalDevice('EMU_FREE')"

    def test_submit_single_sequence(self, mock_client):
        batch = _make_batch(batch_id="batch-xyz")
        mock_client.create_batch.return_value = batch

        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_FREE")
        sequence = '{"foo": 1}'

        job = device.submit(sequence, shots=200)

        assert isinstance(job, PasqalJob)
        assert job.id == "batch-xyz"
        mock_client.create_batch.assert_called_once()
        call_kwargs = mock_client.create_batch.call_args.kwargs
        assert call_kwargs["wait"] is False
        assert call_kwargs["tags"] is None
        assert call_kwargs["jobs"] == [{"runs": 200, "serialized_sequence": '{"foo": 1}'}]
        # Device type must be the enum member for "EMU_FREE".
        assert str(call_kwargs["device_type"]) == "EMU_FREE"

    def test_submit_forwards_tags(self, mock_client):
        """Tags (e.g. a job name) are recorded on the Pasqal batch."""
        mock_client.create_batch.return_value = _make_batch()
        device = PasqalProvider(client=mock_client).get_device("EMU_FREE")
        device.submit('{"stub": true}', tags=["qbraid:job:abc"])
        assert mock_client.create_batch.call_args.kwargs["tags"] == ["qbraid:job:abc"]

    def test_submit_accepts_platform_payload_dict(self, mock_client):
        """The platform's {"sequence_builder": <dict>} payload is serialized to JSON."""
        mock_client.create_batch.return_value = _make_batch()
        device = PasqalProvider(client=mock_client).get_device("EMU_FREE")
        abstract_repr = json.loads(_make_pulser_sequence().to_abstract_repr())

        device.submit({"sequence_builder": abstract_repr}, shots=10)
        payload = mock_client.create_batch.call_args.kwargs["jobs"][0]["serialized_sequence"]
        assert json.loads(payload) == abstract_repr
        # The payload must deserialize back into a Pulser Sequence.
        assert isinstance(Sequence.from_abstract_repr(payload), Sequence)

    def test_submit_accepts_platform_payload_string(self, mock_client):
        """A {"sequence_builder": <str>} payload is passed through unchanged."""
        mock_client.create_batch.return_value = _make_batch()
        device = PasqalProvider(client=mock_client).get_device("EMU_FREE")
        device.submit({"sequence_builder": '{"already": "serialized"}'}, shots=10)
        payload = mock_client.create_batch.call_args.kwargs["jobs"][0]
        assert payload["serialized_sequence"] == '{"already": "serialized"}'

    def test_submit_to_device_unknown_to_pasqal_cloud_raises(self, mock_client, catalog):
        """A catalog device the pinned pasqal-cloud cannot target fails before submission."""
        catalog["EMU_NEW"] = {**CATALOG["EMU_SV"], "device_type": "EMU_NEW"}
        device = PasqalProvider(client=mock_client).get_device("EMU_NEW")
        with pytest.raises(PasqalDeviceError, match="Unknown Pasqal device type"):
            device.submit('{"stub": true}')
        mock_client.create_batch.assert_not_called()

    @pytest.mark.parametrize("bad_input", [{"register": {}}, {"sequence_builder": None}, 42])
    def test_submit_rejects_unknown_payload(self, mock_client, bad_input):
        """A payload that is neither form raises before anything is sent."""
        device = PasqalProvider(client=mock_client).get_device("EMU_FREE")
        with pytest.raises(PasqalDeviceError, match="abstract-representation"):
            device.submit(bad_input)
        mock_client.create_batch.assert_not_called()

    def test_submit_list_of_sequences(self, mock_client):
        batch = _make_batch(batch_id="batch-multi")
        mock_client.create_batch.return_value = batch

        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_TN")
        sequences = ['{"i": 0}', '{"i": 1}']

        job = device.submit(sequences, shots=50)
        assert job.id == "batch-multi"
        jobs_payload = mock_client.create_batch.call_args.kwargs["jobs"]
        assert jobs_payload == [
            {"runs": 50, "serialized_sequence": '{"i": 0}'},
            {"runs": 50, "serialized_sequence": '{"i": 1}'},
        ]

    def test_submit_accepts_pre_serialized_string(self, mock_client):
        mock_client.create_batch.return_value = _make_batch()
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_FREE")

        device.submit('{"already": "serialized"}', shots=10)
        payload = mock_client.create_batch.call_args.kwargs["jobs"][0]
        assert payload["serialized_sequence"] == '{"already": "serialized"}'

    def test_submit_empty_input_raises(self, mock_client):
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_FREE")
        with pytest.raises(PasqalDeviceError, match="at least one"):
            device.submit([])

    def test_submit_wraps_sdk_errors(self, mock_client):
        mock_client.create_batch.side_effect = RuntimeError("api down")
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_FREE")
        with pytest.raises(PasqalDeviceError, match="Failed to submit batch"):
            device.submit('{"stub": true}')

    def test_submit_invalid_shots_raises(self, mock_client):
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_FREE")
        with pytest.raises(PasqalDeviceError, match="`shots` must be a positive integer"):
            device.submit('{"stub": true}', shots=0)


class TestBackendConfiguration:
    """``PasqalDevice.submit(backend_configuration=...)``: the emulator settings sent to Pasqal."""

    def test_submit_defaults_to_the_emulator_settings(self, mock_client):
        """Without a configuration, none is sent and Pasqal uses the emulator's defaults."""
        mock_client.create_batch.return_value = _make_batch()
        PasqalProvider(client=mock_client).get_device("EMU_FREE").submit('{"foo": 1}')
        assert mock_client.create_batch.call_args.kwargs["backend_configuration"] is None

    def test_submit_serializes_an_emulation_config(self, mock_client):
        """A Pulser EmulationConfig is sent as its abstract representation."""
        # pylint: disable-next=import-outside-toplevel
        from pulser.backend import BitStrings, EmulationConfig

        config = EmulationConfig(observables=[BitStrings()], prefer_device_noise_model=True)
        mock_client.create_batch.return_value = _make_batch()
        device = PasqalProvider(client=mock_client).get_device("EMU_FREE")
        device.submit('{"foo": 1}', backend_configuration=config)
        sent = mock_client.create_batch.call_args.kwargs["backend_configuration"]
        assert sent == config.to_abstract_repr()
        assert json.loads(sent)["prefer_device_noise_model"] is True

    @pytest.mark.parametrize("as_dict", [False, True])
    def test_submit_accepts_an_abstract_repr(self, mock_client, as_dict):
        """The abstract representation is accepted as a string, or as the parsed dict."""
        # pylint: disable-next=import-outside-toplevel
        from pulser.backend import BitStrings, EmulationConfig

        abstract_repr = EmulationConfig(observables=[BitStrings()]).to_abstract_repr()
        mock_client.create_batch.return_value = _make_batch()
        device = PasqalProvider(client=mock_client).get_device("EMU_FREE")
        config = json.loads(abstract_repr) if as_dict else abstract_repr
        device.submit('{"foo": 1}', backend_configuration=config)
        sent = mock_client.create_batch.call_args.kwargs["backend_configuration"]
        assert json.loads(sent) == json.loads(abstract_repr)

    def test_submit_rejects_an_unreadable_configuration(self, mock_client):
        """A configuration of the wrong type fails before anything is sent."""
        device = PasqalProvider(client=mock_client).get_device("EMU_FREE")
        with pytest.raises(PasqalDeviceError, match="EmulationConfig"):
            device.submit('{"foo": 1}', backend_configuration=42)
        mock_client.create_batch.assert_not_called()


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------


class TestPasqalJob:
    def test_init_requires_sdk_or_device(self):
        with pytest.raises(PasqalJobError, match="requires either"):
            PasqalJob(job_id="x")

    def test_init_takes_sdk_from_device(self, mock_client):
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_FREE")
        job = PasqalJob(job_id="batch-1", device=device)
        assert job.client is mock_client

    def test_status_polls_batch(self, mock_client):
        mock_client.get_batch.return_value = _make_batch(status="RUNNING")
        job = PasqalJob(job_id="batch-1", client=mock_client)
        assert job.status() == JobStatus.RUNNING

    def test_status_uses_cache_when_terminal(self, mock_client):
        mock_client.get_batch.return_value = _make_batch(status="DONE")
        job = PasqalJob(job_id="batch-1", client=mock_client)
        assert job.status() == JobStatus.COMPLETED
        # Mutate the remote state -- the job should still report COMPLETED.
        mock_client.get_batch.return_value = _make_batch(status="ERROR")
        assert job.status() == JobStatus.COMPLETED

    def test_status_wraps_transport_errors(self, mock_client):
        mock_client.get_batch.side_effect = RuntimeError("oops")
        job = PasqalJob(job_id="batch-1", client=mock_client)
        with pytest.raises(PasqalJobError, match="Unable to retrieve"):
            job.status()

    def test_cancel(self, mock_client):
        job = PasqalJob(job_id="batch-1", client=mock_client)
        job.cancel()
        mock_client.cancel_batch.assert_called_once_with("batch-1")

    def test_cancel_wraps_errors(self, mock_client):
        mock_client.cancel_batch.side_effect = RuntimeError("nope")
        job = PasqalJob(job_id="batch-1", client=mock_client)
        with pytest.raises(PasqalJobError, match="Failed to cancel"):
            job.cancel()

    def test_result_single_job(self, mock_client):
        counts = {"00": 600, "11": 400}
        mock_client.get_batch.return_value = _make_batch(jobs=[_make_job(counter=counts)])
        provider = PasqalProvider(client=mock_client)
        device = provider.get_device("EMU_FREE")

        job = PasqalJob(job_id="batch-1", client=mock_client, device=device)
        result = job.result()
        assert result.success is True
        assert result.device_id == "EMU_FREE"
        assert result.job_id == "batch-1"
        assert result.data.get_counts() == counts

    def test_result_time_stamps(self, mock_client):
        """Results carry the batch's parsed timestamps and execution time in ms."""
        mock_client.get_batch.return_value = _make_batch()
        result = PasqalJob(job_id="batch-1", client=mock_client).result()
        stamps = result.details["time_stamps"]
        assert stamps["createdAt"].isoformat() == "2026-11-05T21:48:13.648700+00:00"
        assert stamps["startedAt"].isoformat() == "2026-11-05T21:48:15.500000+00:00"
        assert stamps["endedAt"].isoformat() == "2026-11-05T21:48:17.750000+00:00"
        assert stamps["executionDuration"] == 2250

    def test_time_stamps_accept_z_suffix(self, mock_client):
        """A UTC timestamp written with a Z suffix parses, including on Python 3.10."""
        mock_client.get_batch.return_value = _make_batch(
            started="2026-11-05T21:48:15.500000Z", ended="2026-11-05T21:48:16.500000Z"
        )
        stamps = PasqalJob(job_id="batch-1", client=mock_client).result().details["time_stamps"]
        assert stamps["startedAt"].utcoffset().total_seconds() == 0
        assert stamps["executionDuration"] == 1000

    def test_unparseable_time_stamp_raises_job_error(self, mock_client):
        """A timestamp Pasqal sends in an unknown form raises PasqalJobError."""
        mock_client.get_batch.return_value = _make_batch(started="yesterday")
        with pytest.raises(PasqalJobError, match="Unrecognized Pasqal timestamp"):
            PasqalJob(job_id="batch-1", client=mock_client).result()

    def test_time_stamps_without_start(self, mock_client):
        """A batch that never started has no start time or duration."""
        mock_client.get_batch.return_value = _make_batch(status="DONE", started=None)
        stamps = PasqalJob(job_id="batch-1", client=mock_client).result().details["time_stamps"]
        assert stamps["startedAt"] is None
        assert stamps["executionDuration"] is None

    def test_status_raises_on_unrecognized_batch_status(self, mock_client):
        """An unknown batch status surfaces as PasqalJobError."""
        mock_client.get_batch.return_value = _make_batch(status="SOMETHING_NEW")
        job = PasqalJob(job_id="batch-1", client=mock_client)
        with pytest.raises(PasqalJobError, match="Unrecognized"):
            job.status()

    def test_result_multi_job_returns_list(self, mock_client):
        counts_a = {"00": 100}
        counts_b = {"01": 100}
        mock_client.get_batch.return_value = _make_batch(
            jobs=[
                _make_job(counter=counts_a, job_id="j1"),
                _make_job(counter=counts_b, job_id="j2"),
            ]
        )
        job = PasqalJob(job_id="batch-1", client=mock_client)
        result = job.result()
        assert result.data.get_counts() == [counts_a, counts_b]

    def test_result_uses_full_result_fallback(self, mock_client):
        job_record = MagicMock()
        job_record.id = "j1"
        job_record.result = None  # primary slot empty
        job_record.full_result = {"counter": {"10": 7}}
        mock_client.get_batch.return_value = _make_batch(jobs=[job_record])
        job = PasqalJob(job_id="batch-1", client=mock_client)
        assert job.result().data.get_counts() == {"10": 7}

    def test_result_raises_on_failure(self, mock_client):
        mock_client.get_batch.return_value = _make_batch(status="ERROR", errors=["bad"])
        job = PasqalJob(job_id="batch-1", client=mock_client)
        with pytest.raises(PasqalJobError, match="did not complete"):
            job.result()

    def test_result_raises_when_no_jobs(self, mock_client):
        mock_client.get_batch.return_value = _make_batch(jobs=[])
        job = PasqalJob(job_id="batch-1", client=mock_client)
        with pytest.raises(PasqalJobError, match="No jobs"):
            job.result()

    def test_result_raises_when_no_counter(self, mock_client):
        job_record = MagicMock()
        job_record.id = "j-empty"
        job_record.result = None
        job_record.full_result = {}  # no counter key
        mock_client.get_batch.return_value = _make_batch(jobs=[job_record])
        job = PasqalJob(job_id="batch-1", client=mock_client)
        with pytest.raises(PasqalJobError, match="no counter result"):
            job.result()


# ---------------------------------------------------------------------------
# pasqal-cloud errors
# ---------------------------------------------------------------------------

# Response bodies Pasqal Cloud returned live (2026-11-05) for a 20-atom sequence on
# EMU_FREE, an unknown batch id, and a cancel of a finished batch.
ATOMS_EXCEEDED_422 = {
    "status": "fail",
    "message": "Unprocessable Content",
    "code": "CB1119",
    "data": {
        "description": [
            {
                "loc": ["jobs", 0, "sequence"],
                "msg": "The sequence's number of atoms (20) exceeds the maximum number of "
                "atoms supported by this device (12)",
            }
        ]
    },
}
BATCH_NOT_FOUND_404 = {
    "status": "fail",
    "message": "Not found.",
    "code": "CB1100",
    "data": {"id": "6aea658f-24fa-48a5-8387-3f63e678cb86", "description": "Batch not found."},
}
CANCEL_DONE_400 = {
    "status": "fail",
    "message": "Bad request.",
    "code": "CB1104",
    "data": {
        "description": "Batch status is not PENDING or RUNNING but DONE and cannot be canceled."
    },
}


def _http_error(status_code: int, body: dict[str, Any]) -> requests.HTTPError:
    """The ``HTTPError`` pasqal-cloud wraps, carrying Pasqal's JSON error body."""
    response = requests.Response()
    response.status_code = status_code
    response._content = json.dumps(body).encode()  # pylint: disable=protected-access
    return requests.HTTPError(f"{status_code} Client Error", response=response)


class TestPasqalCloudErrors:
    """pasqal-cloud's errors derive from ``BaseException``, so ``except Exception`` missed them.

    Each test raises the error pasqal-cloud itself raises for a response Pasqal returned
    live; before the fix it escaped the SDK unwrapped.
    """

    def test_every_base_exception_error_is_caught(self):
        expected = {
            cls
            for cls in vars(pasqal_errors).values()
            if isinstance(cls, type) and issubclass(cls, BaseException)
        }
        caught = _pasqal_cloud_errors()
        assert Exception in caught
        assert all(issubclass(cls, caught) for cls in expected)

    def test_submit_rejected_batch_raises_device_error(self, mock_client):
        mock_client.create_batch.side_effect = pasqal_errors.BatchCreationError(
            _http_error(422, ATOMS_EXCEEDED_422)
        )
        device = PasqalProvider(client=mock_client).get_device("EMU_FREE")
        with pytest.raises(PasqalDeviceError, match="CB1119") as info:
            device.submit('{"stub": true}')
        assert isinstance(info.value.__cause__, pasqal_errors.BatchCreationError)

    def test_status_of_unknown_batch_raises_job_error(self, mock_client):
        mock_client.get_batch.side_effect = pasqal_errors.BatchFetchingError(
            _http_error(404, BATCH_NOT_FOUND_404)
        )
        job = PasqalJob(job_id="batch-1", client=mock_client)
        with pytest.raises(PasqalJobError, match="Batch not found") as info:
            job.status()
        assert isinstance(info.value.__cause__, pasqal_errors.BatchFetchingError)

    def test_cancel_of_finished_batch_raises_job_error(self, mock_client):
        mock_client.cancel_batch.side_effect = pasqal_errors.BatchCancellingError(
            _http_error(400, CANCEL_DONE_400)
        )
        job = PasqalJob(job_id="batch-1", client=mock_client)
        with pytest.raises(PasqalJobError, match="cannot be canceled"):
            job.cancel()

    def test_result_download_failure_raises_job_error(self, mock_client):
        job_record = MagicMock()
        job_record.id = "j1"
        type(job_record).result = PropertyMock(
            side_effect=pasqal_errors.WorkloadResultsConnectionError(
                requests.ConnectionError("connection reset")
            )
        )
        mock_client.get_batch.return_value = _make_batch(jobs=[job_record])
        job = PasqalJob(job_id="batch-1", client=mock_client)
        with pytest.raises(PasqalJobError, match="Unable to download the results"):
            job.result()

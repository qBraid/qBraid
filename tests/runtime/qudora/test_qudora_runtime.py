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

# pylint: disable=redefined-outer-name,protected-access

"""
Unit tests for the QUDORA runtime provider, device, and job classes.

"""

from unittest.mock import MagicMock, patch

import pytest
import qiskit
from pyqasm.exceptions import PyQasmError

from qbraid.runtime import ResourceNotFoundError, Result
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.exceptions import ProgramValidationError
from qbraid.runtime.qudora import (
    QudoraDevice,
    QudoraJob,
    QudoraJobError,
    QudoraProvider,
    QudoraSession,
)
from qbraid.runtime.qudora.provider import _validate_qasm

INVALID_QASM = "OPENQASM 3.0;\nqubit[2] q;\nnotagate q[0];"

TOKEN = "test-token"

BACKENDS = [
    {
        "username": "qamelion",
        "full_name": "Qamelion",
        "max_n_qubits": 32,
        "max_shots": 10000,
        "max_programs_per_job": 10,
        "user_settings_schema": {
            "properties": {
                "measurement_error_probability": {"default": 0.0035},
                "two_qubit_gate_noise_strength": {"default": 1},
                "single_qubit_gate_noise_strength": {"default": 1},
                "dephasing_T2_time": {"default": 60},
            }
        },
        "id": 1,
    },
    {
        "username": "qvls_q1_emulator",
        "full_name": "QVLS-Q1 Emulator",
        "max_n_qubits": 20,
        "max_shots": 10000,
        "max_programs_per_job": 5,
        "user_settings_schema": None,
        "id": 2,
    },
]

QASM2 = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nx q[0];\nmeasure q -> c;'
QASM3 = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nbit[2] c;\nx q[0];\nc = measure q;'


def _response(payload):
    """Build a fake ``requests.Response``-like object with a ``.json()`` method."""
    resp = MagicMock()
    resp.json.return_value = payload
    return resp


def _job_record(status="Completed", result=None, user_error=None):
    """Return a minimal QUDORA ``GET /jobs/`` record for the given status/result."""
    return {
        "status": status,
        "shots": [100],
        "result": result,
        "user_error": user_error,
        "target": "qamelion",
    }


@pytest.fixture(autouse=True)
def _clear_token_env(monkeypatch):
    """Ensure QUDORA env vars never leak into the token/base-url resolution under test."""
    monkeypatch.delenv("QUDORA_API_TOKEN", raising=False)
    monkeypatch.delenv("QUDORA_BASE_URL", raising=False)


@pytest.fixture
def mock_session():
    """A mocked ``QudoraSession`` with sane defaults for backends/status/create."""
    session = MagicMock()
    session.get_backends.return_value = BACKENDS
    session.get_backend_status.return_value = "Idle"
    session.create_job.return_value = 42
    return session


@pytest.fixture
def provider():
    """A ``QudoraProvider`` built with a dummy token (no network on construction)."""
    return QudoraProvider(token=TOKEN)


@pytest.fixture
def profile(provider):
    """A ``TargetProfile`` for the first sample backend."""
    return provider._build_profile(BACKENDS[0])


@pytest.fixture
def device(profile, mock_session):
    """A ``QudoraDevice`` backed by the mocked session."""
    return QudoraDevice(profile, mock_session)


class TestQudoraSession:
    """Tests for the QUDORA REST session."""

    def test_requires_token(self):
        """Constructing a session without a token (or env var) raises ValueError."""
        with pytest.raises(ValueError, match="QUDORA API token is required"):
            QudoraSession()

    def test_token_from_env(self, monkeypatch):
        """The token is read from QUDORA_API_TOKEN and used as a Bearer header."""
        monkeypatch.setenv("QUDORA_API_TOKEN", "envtok")
        session = QudoraSession()
        assert session.token == "envtok"
        assert session.auth_headers["Authorization"] == "Bearer envtok"

    def test_base_url_default_and_override(self):
        """base_url defaults to api.qudora.com and honors an explicit override (trailing / stripped)."""
        assert QudoraSession(TOKEN).base_url == "https://api.qudora.com"
        assert QudoraSession(TOKEN, base_url="https://staging.qudora.com/").base_url == (
            "https://staging.qudora.com"
        )

    def test_get_backends(self):
        """get_backends() issues GET /backends/ and returns the decoded list."""
        session = QudoraSession(TOKEN)
        with patch.object(session, "get", return_value=_response(BACKENDS)) as mock_get:
            assert session.get_backends() == BACKENDS
        mock_get.assert_called_once_with("/backends/")

    def test_get_backend_status(self):
        """get_backend_status() issues GET /backends/status/{id} and returns the status name."""
        session = QudoraSession(TOKEN)
        with patch.object(session, "get", return_value=_response("Idle")) as mock_get:
            assert session.get_backend_status(1) == "Idle"
        mock_get.assert_called_once_with("/backends/status/1")

    def test_create_job(self):
        """create_job() POSTs the body as JSON to /jobs/ and returns the integer id."""
        session = QudoraSession(TOKEN)
        with patch.object(session, "post", return_value=_response(7)) as mock_post:
            assert session.create_job({"target": "qamelion"}) == 7
        mock_post.assert_called_once_with("/jobs/", json={"target": "qamelion"})

    def test_get_job_returns_first_element(self):
        """get_job() filters GET /jobs/ by job_id and returns the first array element."""
        session = QudoraSession(TOKEN)
        record = _job_record("Completed")
        with patch.object(session, "get", return_value=_response([record])) as mock_get:
            assert session.get_job(5, include_results=True) == record
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["job_id"] == 5
        assert kwargs["params"]["include_results"] is True

    def test_get_job_not_found(self):
        """An empty GET /jobs/ array means the job id does not exist -> ResourceNotFoundError."""
        session = QudoraSession(TOKEN)
        with patch.object(session, "get", return_value=_response([])):
            with pytest.raises(ResourceNotFoundError, match="Job '5' not found"):
                session.get_job(5)

    def test_cancel_job(self):
        """cancel_job() issues PUT /jobs/ with status_name=Canceled."""
        session = QudoraSession(TOKEN)
        with patch.object(session, "put", return_value=_response(None)) as mock_put:
            session.cancel_job(9)
        mock_put.assert_called_once_with("/jobs/", params={"job_id": 9, "status_name": "Canceled"})

    def test_configures_retries(self):
        """Retries are enabled so a transient connection drop during polling recovers."""
        session = QudoraSession(TOKEN)
        adapter = session.get_adapter("https://api.qudora.com")
        assert adapter.max_retries.total == 3
        assert adapter.max_retries.connect == 1


class TestQudoraProvider:
    """Tests for the QUDORA provider."""

    def test_build_profile(self, profile):
        """_build_profile() maps a backend record onto the expected TargetProfile fields."""
        assert profile.device_id == "qamelion"
        assert profile.num_qubits == 32
        assert profile.simulator is True
        assert profile.provider_name == "QUDORA"
        assert profile.get("qudora_backend_id") == 1
        assert profile.get("max_programs_per_job") == 10
        assert [spec.alias for spec in profile.program_spec] == ["qasm2", "qasm3"]

    def test_get_devices(self, provider):
        """get_devices() builds one device per backend returned by the session."""
        with patch.object(provider.session, "get_backends", return_value=BACKENDS):
            devices = provider.get_devices()
        assert len(devices) == 2
        assert {device.id for device in devices} == {"qamelion", "qvls_q1_emulator"}

    def test_get_device(self, provider):
        """get_device() finds a backend by its username device id."""
        with patch.object(provider.session, "get_backends", return_value=BACKENDS):
            device = provider.get_device("qvls_q1_emulator")
        assert isinstance(device, QudoraDevice)
        assert device.id == "qvls_q1_emulator"
        assert device.num_qubits == 20

    def test_get_device_not_found(self, provider):
        """get_device() raises ResourceNotFoundError when the username is absent from the listing."""
        with patch.object(provider.session, "get_backends", return_value=BACKENDS):
            with pytest.raises(ResourceNotFoundError, match="Device 'nope' not found"):
                provider.get_device("nope")

    def test_hash_is_stable(self, provider):
        """The provider hash is stable across calls (providers are cached)."""
        assert hash(provider) == hash(provider)


class TestQudoraDevice:
    """Tests for the QUDORA device."""

    @pytest.mark.parametrize(
        "status_name, expected",
        [
            ("Idle", DeviceStatus.ONLINE),
            ("Executing", DeviceStatus.ONLINE),
            ("Calibrating", DeviceStatus.UNAVAILABLE),
            ("Unresponsive", DeviceStatus.OFFLINE),
            ("Something", DeviceStatus.UNAVAILABLE),
        ],
    )
    def test_status_mapping(self, device, status_name, expected):
        """BackendStatusName values map to the expected DeviceStatus."""
        device.session.get_backend_status.return_value = status_name
        assert device.status() == expected

    def test_status_without_backend_id(self, provider, mock_session):
        """Without a backend id, a listed device is reported ONLINE without calling the status endpoint."""
        backend = {key: value for key, value in BACKENDS[1].items() if key != "id"}
        device = QudoraDevice(provider._build_profile(backend), mock_session)
        assert device.status() == DeviceStatus.ONLINE
        mock_session.get_backend_status.assert_not_called()

    def test_detect_language(self, device):
        """_detect_language() reads the OpenQASM version from the header, else raises."""
        assert device._detect_language(QASM2) == "OpenQASM2"
        assert device._detect_language(QASM3) == "OpenQASM3"
        with pytest.raises(ValueError, match="Could not determine"):
            device._detect_language("h q[0];")

    def test_available_settings(self, device):
        """available_settings() exposes the backend's user_settings_schema properties."""
        settings = device.available_settings()
        assert settings["measurement_error_probability"]["default"] == 0.0035
        assert set(settings) == {
            "measurement_error_probability",
            "two_qubit_gate_noise_strength",
            "single_qubit_gate_noise_strength",
            "dephasing_T2_time",
        }

    def test_available_settings_empty_when_absent(self, provider, mock_session):
        """available_settings() returns an empty dict when the backend exposes no schema."""
        device = QudoraDevice(provider._build_profile(BACKENDS[1]), mock_session)
        assert device.available_settings() == {}

    def test_submit_body(self, device):
        """submit() builds the POST /jobs/ body and returns a QudoraJob with the returned id."""
        job = device.submit(QASM2, shots=256, name="my-job")
        body = device.session.create_job.call_args.args[0]
        assert body == {
            "name": "my-job",
            "target": "qamelion",
            "language": "OpenQASM2",
            "shots": [256],
            "input_data": [QASM2],
            "backend_settings": {},
        }
        assert isinstance(job, QudoraJob)
        assert job.id == "42"

    def test_submit_default_name(self, device):
        """submit() defaults the job name to 'qbraid' when none is given."""
        device.submit(QASM3)
        assert device.session.create_job.call_args.args[0]["name"] == "qbraid"

    def test_submit_batch(self, device):
        """submit() with a list of programs sends per-program shots and one input_data entry each."""
        device.submit([QASM3, QASM3], shots=10)
        body = device.session.create_job.call_args.args[0]
        assert body["shots"] == [10, 10]
        assert body["language"] == "OpenQASM3"
        assert len(body["input_data"]) == 2

    def test_submit_backend_settings(self, device):
        """submit() forwards backend_settings (noise parameters) into the job body."""
        settings = {
            "measurement_error_probability": 0.01,
            "two_qubit_gate_noise_strength": 0.5,
            "single_qubit_gate_noise_strength": 0.5,
            "dephasing_T2_time": 45,
        }
        device.submit(QASM2, backend_settings=settings)
        body = device.session.create_job.call_args.args[0]
        assert body["backend_settings"] == settings

    def test_submit_mixed_language_raises(self, device):
        """A batch mixing OpenQASM2 and OpenQASM3 programs is rejected."""
        with pytest.raises(ValueError, match="same OpenQASM version"):
            device.submit([QASM2, QASM3])

    def test_submit_exceeds_max_programs(self, provider, mock_session):
        """Submitting more programs than max_programs_per_job is rejected."""
        device = QudoraDevice(provider._build_profile(BACKENDS[1]), mock_session)
        with pytest.raises(ValueError, match="exceeds the device's maximum"):
            device.submit([QASM2] * 6)

    def test_submit_fails_loud_on_missing_job_id(self, device):
        """submit() raises if the API response carries no job id (no silent fallback)."""
        device.session.create_job.return_value = None
        with pytest.raises(ValueError, match="did not return a job id"):
            device.submit(QASM2)

    @pytest.mark.parametrize("run_input, expected", [(QASM2, "OpenQASM2"), (QASM3, "OpenQASM3")])
    def test_run_qasm(self, device, run_input, expected):
        """run() validates (pyqasm) and submits a qasm string with the auto-detected language."""
        device.run(run_input, shots=100)
        assert device.session.create_job.call_args.args[0]["language"] == expected

    def test_run_qiskit_transpiles_to_qasm(self, device):
        """run() transpiles a Qiskit circuit down to an OpenQASM3 string before submission."""
        circuit = qiskit.QuantumCircuit(2)
        circuit.x(0)
        circuit.measure_all()
        device.run(circuit, shots=100)
        body = device.session.create_job.call_args.args[0]
        assert body["language"] == "OpenQASM3"
        assert body["input_data"][0].lstrip().startswith("OPENQASM 3")

    def test_run_rejects_invalid_qasm(self, device):
        """Invalid QASM is rejected during run() validation before anything is submitted."""
        with pytest.raises((ProgramValidationError, PyQasmError)):
            device.run(INVALID_QASM)
        device.session.create_job.assert_not_called()

    def test_validate_qasm_hook(self):
        """The pyqasm validate hook passes valid QASM and raises ValueError on invalid QASM."""
        _validate_qasm(QASM2)
        _validate_qasm(QASM3)
        with pytest.raises(ValueError, match="Invalid OpenQASM program for QUDORA"):
            _validate_qasm(INVALID_QASM)


class TestQudoraJob:
    """Tests for the QUDORA job."""

    @pytest.mark.parametrize(
        "status_name, expected",
        [
            ("Submitted", JobStatus.QUEUED),
            ("Queuing", JobStatus.QUEUED),
            ("Uncompiled", JobStatus.QUEUED),
            ("Reserved", JobStatus.QUEUED),
            ("Running", JobStatus.RUNNING),
            ("Cancelling", JobStatus.CANCELLING),
            ("Completed", JobStatus.COMPLETED),
            ("Canceled", JobStatus.CANCELLED),
            ("Deleted", JobStatus.CANCELLED),
            ("Failed", JobStatus.FAILED),
            ("Bogus", JobStatus.UNKNOWN),
        ],
    )
    def test_map_status(self, status_name, expected):
        """QUDORA JobStatusName values map to the expected qBraid JobStatus."""
        assert QudoraJob._map_status(status_name) == expected

    def test_status(self, mock_session):
        """status() fetches the job record and maps its status."""
        mock_session.get_job.return_value = _job_record("Running")
        job = QudoraJob("42", session=mock_session)
        assert job.status() == JobStatus.RUNNING

    def test_cancel(self, mock_session):
        """cancel() delegates to the session's cancel_job with the job id."""
        job = QudoraJob("42", session=mock_session)
        job.cancel()
        mock_session.cancel_job.assert_called_once_with("42")

    def test_result_success_single(self, mock_session, device):
        """result() parses a single-circuit histogram into GateModelResultData."""
        mock_session.get_job.return_value = _job_record("Completed", result=['{"01": 100}'])
        job = QudoraJob("42", session=mock_session, device=device, shots=100)
        result = job.result()
        assert isinstance(result, Result)
        assert result.success is True
        assert result.device_id == "qamelion"
        assert result.data.measurement_counts == {"01": 100}

    def test_result_multi_circuit(self, mock_session, device):
        """result() parses a multi-circuit job into a list of histograms."""
        mock_session.get_job.return_value = _job_record(
            "Completed", result=['{"0": 50}', '{"1": 50}']
        )
        job = QudoraJob("42", session=mock_session, device=device, shots=50)
        assert job.result().data.measurement_counts == [{"0": 50}, {"1": 50}]

    def test_result_bit_ordering_preserved(self, mock_session, device):
        """QUDORA's bitstring key orientation is forwarded unchanged (no silent reversal)."""
        # An X on q0 only; pin the orientation so a future reordering would fail this test.
        mock_session.get_job.return_value = _job_record("Completed", result=['{"01": 1000}'])
        job = QudoraJob("42", session=mock_session, device=device, shots=1000)
        counts = job.result().data.measurement_counts
        assert counts == {"01": 1000}
        assert "10" not in counts

    def test_result_failure_raises(self, mock_session, device):
        """A non-completed job surfaces its user_error via QudoraJobError."""
        mock_session.get_job.return_value = _job_record("Failed", user_error="bad circuit")
        job = QudoraJob("42", session=mock_session, device=device)
        with pytest.raises(QudoraJobError, match="bad circuit"):
            job.result()

    def test_result_missing_data_raises(self, mock_session, device):
        """A completed job with no result payload raises QudoraJobError."""
        mock_session.get_job.return_value = _job_record("Completed", result=[])
        job = QudoraJob("42", session=mock_session, device=device)
        with pytest.raises(QudoraJobError, match="no result data"):
            job.result()

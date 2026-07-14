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

"""
Unit tests for the AQT runtime provider, device, and job classes.

All AQT arnica HTTP calls are mocked; no network access occurs.

"""

import sys
import types
from unittest.mock import MagicMock

import pytest

from qbraid.programs import ProgramSpec
from qbraid.runtime.aqt import AQTDevice, AQTJob, AQTJobError, AQTProvider, AQTSession
from qbraid.runtime.aqt.device import _build_submit_body
from qbraid.runtime.aqt.job import _samples_to_counts
from qbraid.runtime.aqt.provider import _resolve_access_token
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.exceptions import ResourceNotFoundError

# A serialized per-circuit payload as produced by the ``qiskit_to_aqt`` serialize hook.
_SERIALIZED_CIRCUIT = {
    "quantum_circuit": [
        {"qubit": 0, "phi": 0.0, "theta": 1.0, "operation": "R"},
        {"operation": "MEASURE"},
    ],
    "number_of_qubits": 1,
}


@pytest.fixture
def mock_session():
    """A fully mocked AQTSession (no network)."""
    session = MagicMock(spec=AQTSession)
    session.get_resource.return_value = {"id": "sim1", "status": "online", "available_qubits": 20}
    session.submit_job.return_value = {"job": {"job_id": "job-1"}}
    return session


@pytest.fixture
def profile():
    return AQTProvider._build_profile(
        {"id": "sim1", "type": "simulator", "available_qubits": 20}, "default"
    )


@pytest.fixture
def device(profile, mock_session):
    return AQTDevice(profile, mock_session)


# --------------------------------------------------------------------------- auth


def test_session_explicit_token_skips_resolution(monkeypatch):
    """An explicit access_token short-circuits _resolve_access_token entirely."""

    def _fail(*args, **kwargs):
        raise AssertionError("_resolve_access_token should not be called for an explicit token")

    monkeypatch.setattr("qbraid.runtime.aqt.provider._resolve_access_token", _fail)
    session = AQTSession(access_token="explicit-token")
    assert session.access_token == "explicit-token"


def test_resolve_access_token_env(monkeypatch):
    monkeypatch.setenv("AQT_ACCESS_TOKEN", "env-token")
    assert _resolve_access_token() == "env-token"


def test_resolve_access_token_client_credentials_from_env(monkeypatch):
    """client_id/client_secret fall back to AQT_CLIENT_ID/AQT_CLIENT_SECRET for the CC flow."""
    pytest.importorskip("aqt_connector")
    monkeypatch.delenv("AQT_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("AQT_CLIENT_ID", "cid")
    monkeypatch.setenv("AQT_CLIENT_SECRET", "csecret")

    captured = {}

    def fake_get_access_token(app):
        captured["client_id"] = app.config.client_id
        captured["client_secret"] = app.config.client_secret
        return None  # no stored session -> falls through to client-credentials

    monkeypatch.setattr("aqt_connector.get_access_token", fake_get_access_token)
    monkeypatch.setattr("aqt_connector.log_in", lambda app: "cc-token")

    assert _resolve_access_token() == "cc-token"
    assert captured == {"client_id": "cid", "client_secret": "csecret"}


# --------------------------------------------------------------------------- provider


def test_build_profile_fields():
    profile = AQTProvider._build_profile(
        {"id": "ibex", "type": "device", "available_qubits": 12}, "aqt"
    )
    assert profile.device_id == "aqt/ibex"
    assert profile.simulator is False
    assert profile.num_qubits == 12
    assert profile.provider_name == "AQT"
    assert profile.get("aqt_workspace_id") == "aqt"
    assert profile.get("aqt_resource_id") == "ibex"
    spec = profile.program_spec
    # The device targets the qiskit alias; the AQT payload is produced by the serialize hook.
    assert isinstance(spec, ProgramSpec) and spec.alias == "qiskit"


def test_get_devices(monkeypatch):
    provider = AQTProvider(access_token="tok")
    provider.session.get_workspaces = MagicMock(
        return_value=[{"id": "default", "resources": [{"id": "sim1", "type": "simulator"}]}]
    )
    provider.session.get_resource = MagicMock(
        return_value={"id": "sim1", "type": "simulator", "available_qubits": 20, "status": "online"}
    )
    devices = provider.get_devices()
    assert len(devices) == 1
    assert isinstance(devices[0], AQTDevice)
    assert devices[0].id == "default/sim1"


def test_get_device(monkeypatch):
    provider = AQTProvider(access_token="tok")
    provider.session.get_resource = MagicMock(
        return_value={"id": "sim1", "type": "simulator", "available_qubits": 20}
    )
    device = provider.get_device("default/sim1")
    assert isinstance(device, AQTDevice)
    assert device.id == "default/sim1"
    assert device.workspace_id == "default"
    assert device.resource_id == "sim1"


def test_get_device_invalid_id():
    provider = AQTProvider(access_token="tok")
    with pytest.raises(ResourceNotFoundError):
        provider.get_device("no-separator")


def test_provider_hash():
    provider = AQTProvider(access_token="tok")
    assert isinstance(hash(provider), int)


# --------------------------------------------------------------------------- device


@pytest.mark.parametrize(
    "status,expected",
    [
        ("online", DeviceStatus.ONLINE),
        ("offline", DeviceStatus.OFFLINE),
        ("maintenance", DeviceStatus.UNAVAILABLE),
        ("unavailable", DeviceStatus.UNAVAILABLE),
    ],
)
def test_device_status(device, mock_session, status, expected):
    mock_session.get_resource.return_value = {"status": status}
    assert device.status() == expected


def test_device_status_unknown(device, mock_session):
    mock_session.get_resource.return_value = {"status": "banana"}
    with pytest.raises(ValueError):
        device.status()


def test_build_submit_body_single():
    body = _build_submit_body([_SERIALIZED_CIRCUIT], shots=64, label="demo")
    assert body["job_type"] == "quantum_circuit"
    assert body["label"] == "demo"
    circuits = body["payload"]["circuits"]
    assert len(circuits) == 1
    assert circuits[0]["repetitions"] == 64
    assert circuits[0]["number_of_qubits"] == 1
    assert circuits[0]["quantum_circuit"] == _SERIALIZED_CIRCUIT["quantum_circuit"]


def test_device_submit_returns_job(device, mock_session):
    job = device.submit(_SERIALIZED_CIRCUIT, shots=100)
    assert isinstance(job, AQTJob)
    assert job.id == "job-1"
    mock_session.submit_job.assert_called_once()
    ws, res, body = mock_session.submit_job.call_args.args
    assert (ws, res) == ("default", "sim1")
    assert body["payload"]["circuits"][0]["repetitions"] == 100


def test_device_submit_missing_job_id(device, mock_session):
    mock_session.submit_job.return_value = {"job": {}}
    with pytest.raises(ValueError):
        device.submit(_SERIALIZED_CIRCUIT)


def test_device_run_end_to_end(device, mock_session):
    """Full run(): qiskit circuit -> serialize hook -> aqt payload -> submit."""
    pytest.importorskip("qiskit_aqt_provider")
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    job = device.run(qc, shots=250)
    assert isinstance(job, AQTJob)
    _ws, _res, body = mock_session.submit_job.call_args.args
    circuit = body["payload"]["circuits"][0]
    assert circuit["repetitions"] == 250
    assert circuit["number_of_qubits"] == 2
    assert circuit["quantum_circuit"][-1]["operation"] == "MEASURE"


def test_device_run_from_non_qiskit_input(device, mock_session):
    """A non-qiskit program (OpenQASM 3) is routed to qiskit by the transpiler, then serialized."""
    pytest.importorskip("qiskit_aqt_provider")
    qasm3 = """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
c = measure q;
"""
    job = device.run(qasm3, shots=100)
    assert isinstance(job, AQTJob)
    circuit = mock_session.submit_job.call_args.args[2]["payload"]["circuits"][0]
    assert circuit["number_of_qubits"] == 2
    assert {op["operation"] for op in circuit["quantum_circuit"]} <= {"RZ", "R", "RXX", "MEASURE"}


def test_qiskit_to_aqt_converter():
    """The serialize hook decomposes to the AQT native basis with API-valid angles."""
    pytest.importorskip("qiskit_aqt_provider")
    from qiskit import QuantumCircuit

    from qbraid.runtime.aqt.converter import qiskit_to_aqt

    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 2)  # non-adjacent -> exercises the AQT angle-wrapping passes
    qc.rx(-1.7, 1)
    qc.measure_all()

    payload = qiskit_to_aqt(qc)
    assert payload["number_of_qubits"] == 3
    ops = payload["quantum_circuit"]
    assert {op["operation"] for op in ops} <= {"RZ", "R", "RXX", "MEASURE"}
    assert ops[-1]["operation"] == "MEASURE"
    for op in ops:
        if op["operation"] == "R":
            assert op["theta"] >= 0
        if op["operation"] == "RXX":
            assert 0 <= op["theta"] <= 0.5


# --------------------------------------------------------------------------- job


@pytest.mark.parametrize(
    "status,expected",
    [
        ("queued", JobStatus.QUEUED),
        ("ongoing", JobStatus.RUNNING),
        ("finished", JobStatus.COMPLETED),
        ("error", JobStatus.FAILED),
        ("cancelled", JobStatus.CANCELLED),
        ("weird", JobStatus.UNKNOWN),
    ],
)
def test_job_map_status(status, expected):
    assert AQTJob._map_status(status) == expected


def test_job_status(mock_session):
    mock_session.get_result.return_value = {"response": {"status": "ongoing"}}
    job = AQTJob("job-1", session=mock_session)
    assert job.status() == JobStatus.RUNNING


def test_job_cancel(mock_session):
    job = AQTJob("job-1", session=mock_session)
    job.cancel()
    mock_session.cancel_job.assert_called_once_with("job-1")


def test_samples_to_counts_single():
    counts = _samples_to_counts({"0": [[1, 0, 1], [1, 0, 1], [0, 0, 0]]})
    assert counts == {"101": 2, "000": 1}


def test_samples_to_counts_multi():
    counts = _samples_to_counts({"0": [[0]], "1": [[1], [1]]})
    assert counts == [{"0": 1}, {"1": 2}]


def test_job_result_success(device, mock_session):
    mock_session.get_result.return_value = {
        "job": {"workspace_id": "default", "resource_id": "sim1"},
        "response": {"status": "finished", "result": {"0": [[1, 0], [1, 0], [0, 1]]}},
    }
    job = AQTJob("job-1", session=mock_session, device=device)
    result = job.result()
    assert result.success is True
    assert result.data.get_counts() == {"10": 2, "01": 1}


def test_job_result_failure(mock_session):
    mock_session.get_result.return_value = {
        "job": {},
        "response": {"status": "error", "message": "calibration drift"},
    }
    job = AQTJob("job-1", session=mock_session)
    with pytest.raises(AQTJobError, match="calibration drift"):
        job.result()


def test_job_session_none_fallback(monkeypatch):
    """AQTJob(session=None) lazily builds a default AQTSession."""
    sentinel = MagicMock(name="AQTSession()")
    monkeypatch.setattr("qbraid.runtime.aqt.provider.AQTSession", lambda: sentinel)
    assert AQTJob("job-1").session is sentinel


def test_job_result_without_device_uses_metadata(mock_session):
    """With no attached device, the result device_id is derived from arnica job metadata."""
    mock_session.get_result.return_value = {
        "job": {"workspace_id": "ws", "resource_id": "res"},
        "response": {"status": "finished", "result": {"0": [[0], [1]]}},
    }
    result = AQTJob("job-1", session=mock_session).result()
    assert result.device_id == "ws/res"


# --------------------------------------------------------------------------- AQTSession HTTP


def _mock_http_session():
    """A real AQTSession with its ``requests`` transport (get/post/delete) mocked out."""
    session = AQTSession(access_token="tok")
    session.get = MagicMock()
    session.post = MagicMock()
    session.delete = MagicMock()
    return session


def test_session_base_url_and_token():
    session = AQTSession(access_token="tok", arnica_url="https://example.test/api")
    assert session.base_url == "https://example.test/api/v1"
    assert session.access_token == "tok"


def test_session_http_methods():
    session = _mock_http_session()

    session.get.return_value.json.return_value = [{"id": "w"}]
    assert session.get_workspaces() == [{"id": "w"}]
    session.get.assert_called_with("/workspaces")

    session.get.return_value.json.return_value = {"id": "sim1", "status": "online"}
    assert session.get_resource("sim1")["status"] == "online"

    session.post.return_value.json.return_value = {"job": {"job_id": "j1"}}
    assert session.submit_job("ws", "res", {"payload": {}}) == {"job": {"job_id": "j1"}}

    session.get.return_value.json.return_value = {"response": {"status": "finished"}}
    assert session.get_result("j1")["response"]["status"] == "finished"

    session.cancel_job("j1")
    session.delete.assert_called_once_with("/jobs/j1")


def test_session_get_resource_not_found():
    session = _mock_http_session()
    session.get.side_effect = RuntimeError("boom")
    with pytest.raises(ResourceNotFoundError):
        session.get_resource("missing")


# --------------------------------------------------------------------------- auth resolution


def _fake_aqt_connector(stored=None, cc_token="cc-token"):
    """A stand-in ``aqt_connector`` module so the auth path runs without the real dependency."""
    module = types.ModuleType("aqt_connector")

    class _Config:  # pylint: disable=too-few-public-methods
        def __init__(self):
            self.client_id = None
            self.client_secret = None

    module.ArnicaConfig = _Config
    module.ArnicaApp = lambda config: types.SimpleNamespace(config=config)
    module.get_access_token = lambda app: stored
    module.log_in = lambda app: cc_token
    return module


def test_resolve_token_stored_session(monkeypatch):
    monkeypatch.delenv("AQT_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("AQT_CLIENT_ID", raising=False)
    monkeypatch.delenv("AQT_CLIENT_SECRET", raising=False)
    monkeypatch.setitem(sys.modules, "aqt_connector", _fake_aqt_connector(stored="stored"))
    assert _resolve_access_token() == "stored"


def test_resolve_token_client_credentials_from_env(monkeypatch):
    monkeypatch.delenv("AQT_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("AQT_CLIENT_ID", "cid")
    monkeypatch.setenv("AQT_CLIENT_SECRET", "sec")
    monkeypatch.setitem(
        sys.modules, "aqt_connector", _fake_aqt_connector(stored=None, cc_token="cc")
    )
    assert _resolve_access_token() == "cc"


def test_resolve_token_none_available_raises(monkeypatch):
    monkeypatch.delenv("AQT_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("AQT_CLIENT_ID", raising=False)
    monkeypatch.delenv("AQT_CLIENT_SECRET", raising=False)
    monkeypatch.setitem(sys.modules, "aqt_connector", _fake_aqt_connector(stored=None))
    with pytest.raises(ValueError, match="No AQT access token"):
        _resolve_access_token()


def test_resolve_token_missing_aqt_connector(monkeypatch):
    monkeypatch.delenv("AQT_ACCESS_TOKEN", raising=False)
    monkeypatch.setitem(sys.modules, "aqt_connector", None)  # forces ImportError on import
    with pytest.raises(ValueError, match="aqt-connector"):
        _resolve_access_token()


# --------------------------------------------------------------------------- device + converter edges


def test_device_str(device):
    assert str(device) == "AQTDevice('default/sim1')"


def test_device_submit_ignores_runtime_options(device):
    """runtime_options are accepted and ignored (debug-logged)."""
    job = device.submit(_SERIALIZED_CIRCUIT, shots=10, runtime_options={"foo": "bar"})
    assert isinstance(job, AQTJob)


def test_qiskit_to_aqt_mocked_vendor(monkeypatch):
    """Cover the serialize hook without the real qiskit-aqt-provider installed."""
    from qbraid.runtime.aqt import converter

    fake_payload = MagicMock()
    fake_payload.model_dump.return_value = [{"operation": "MEASURE"}]
    fake_mod = types.ModuleType("qiskit_aqt_provider.circuit_to_aqt")
    fake_mod.qiskit_to_aqt_circuit = lambda transpiled: fake_payload
    monkeypatch.setitem(sys.modules, "qiskit_aqt_provider", types.ModuleType("qiskit_aqt_provider"))
    monkeypatch.setitem(sys.modules, "qiskit_aqt_provider.circuit_to_aqt", fake_mod)

    fake_qiskit = MagicMock()
    monkeypatch.setattr(converter, "qiskit", fake_qiskit)

    circuit = MagicMock()
    circuit.num_qubits = 3
    payload = converter.qiskit_to_aqt(circuit)
    assert payload == {"quantum_circuit": [{"operation": "MEASURE"}], "number_of_qubits": 3}
    fake_qiskit.transpile.assert_called_once()

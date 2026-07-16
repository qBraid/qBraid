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
Unit tests for the AQT runtime provider, device, and job classes, the ``qiskit -> aqt``
transpiler conversion, the ``AQTProgram`` wrapper, and the ``aqt`` program-type registration.

The AQT native circuit is now produced entirely by the ``qiskit -> aqt`` transpiler edge (no
device serialize hook, no ``qiskit-aqt-provider`` dependency). ``aqt-connector`` is a real
installed dependency: its HTTP session methods are mocked, and its auth functions are
monkeypatched on the ``qbraid.runtime.aqt.provider`` module. No network access occurs.

"""

from __future__ import annotations

import math
import types
import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
from aqt_connector.models.circuits import Circuit, QuantumCircuit
from aqt_connector.models.operations import GateR, GateRXX, GateRZ, Measure, OperationModel
from qbraid_core.exceptions import RequestsApiError
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit

from qbraid.programs import (
    QPROGRAM_ALIASES,
    QPROGRAM_REGISTRY,
    ProgramSpec,
    get_program_type_alias,
)
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.aqt import AQTProgram
from qbraid.runtime.aqt import AQTDevice, AQTJob, AQTJobError, AQTProvider, AQTSession
from qbraid.runtime.aqt.job import _samples_to_counts
from qbraid.runtime.aqt.provider import _resolve_access_token
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.transpiler import ConversionGraph, transpile
from qbraid.transpiler.conversions.qiskit.qiskit_to_aqt import (
    WrapRxxAngles,
    _qiskit_to_aqt_circuit,
    rewrite_rx_as_r,
    wrap_rxx_angle,
)

# ---------------------------------------------------------------------------
# helpers / builders
# ---------------------------------------------------------------------------


def _aqt_quantum_circuit(number_of_qubits: int = 2) -> QuantumCircuit:
    """Build a minimal, API-valid native AQT ``QuantumCircuit`` from real ``aqt_connector`` models.

    Angles are already in the API's units of pi and within the accepted ranges, so the model
    validates on construction. ``repetitions`` is the placeholder the device overwrites.
    """
    circuit = Circuit(
        root=[
            OperationModel(root=GateRZ(phi=0.5, qubit=0)),
            OperationModel(root=GateR(phi=0.0, theta=0.5, qubit=0)),
            OperationModel(root=GateRXX(theta=0.5, qubits=[0, 1])),
            OperationModel(root=Measure()),
        ]
    )
    return QuantumCircuit(repetitions=1, quantum_circuit=circuit, number_of_qubits=number_of_qubits)


def _result_payload(
    status: str,
    *,
    result: Any = None,
    message: str = "",
    workspace_id: str = "ws",
    resource_id: str = "res",
) -> dict[str, Any]:
    """Build a raw ``get_result`` dict that validates as an arnica ``ResultResponse``."""
    response: dict[str, Any] = {"status": status}
    if result is not None:
        response["result"] = result
    if status == "error":
        response["message"] = message
    if status == "ongoing":
        response["finished_count"] = 0
    return {
        "job": {
            "job_id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "resource_id": resource_id,
        },
        "response": response,
    }


@pytest.fixture
def mock_session() -> MagicMock:
    """A fully mocked ``AQTSession`` (no network)."""
    session = MagicMock(spec=AQTSession)
    session.get_resource.return_value = {"id": "sim1", "status": "online", "available_qubits": 20}
    session.submit_job.return_value = {"job": {"job_id": "job-1"}}
    return session


@pytest.fixture
def profile():
    """A ``TargetProfile`` for the ``default/sim1`` simulator resource."""
    return AQTProvider._build_profile(
        {"id": "sim1", "type": "simulator", "available_qubits": 20}, "default"
    )


@pytest.fixture
def device(profile, mock_session) -> AQTDevice:
    """An ``AQTDevice`` backed by the mocked session."""
    return AQTDevice(profile, mock_session)


# ---------------------------------------------------------------------------
# transpiler edge
# ---------------------------------------------------------------------------


def test_conversion_graph_has_qiskit_to_aqt_edge():
    """The ``qiskit -> aqt`` edge is registered in the conversion graph."""
    assert ConversionGraph().has_edge("qiskit", "aqt") is True


def test_transpile_qiskit_to_aqt_returns_native_circuit():
    """``transpile(qiskit_circuit, "aqt")`` returns a native ``aqt_connector`` circuit."""
    qc = QiskitCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    out = transpile(qc, "aqt")
    assert type(out).__module__ == "aqt_connector.models.circuits"
    assert type(out).__name__ == "QuantumCircuit"
    assert out.number_of_qubits == 2
    assert out.repetitions == 1
    assert get_program_type_alias(out) == "aqt"


def test_transpile_ghz_produces_valid_circuit_with_measurement_last():
    """A GHZ transpile decomposes to the AQT native basis and validates; measurement is last."""
    ghz = QiskitCircuit(3)
    ghz.h(0)
    ghz.cx(0, 1)
    ghz.cx(1, 2)
    ghz.measure_all()

    out = transpile(ghz, "aqt")
    assert out.number_of_qubits == 3

    ops = out.quantum_circuit.root
    op_names = {type(op.root).__name__ for op in ops}
    assert op_names <= {"GateRZ", "GateR", "GateRXX", "Measure"}
    assert type(ops[-1].root).__name__ == "Measure"

    # The produced native circuit re-validates against the aqt_connector model.
    QuantumCircuit.model_validate(out.model_dump())


def test_transpile_non_adjacent_cx_wraps_angles_into_api_ranges():
    """A non-adjacent CX (+ negative rx) exercises the angle-wrapping passes; angles stay in range.

    Angles are emitted in units of pi: ``R.theta in [0, 1]`` and ``RXX.theta in [0, 0.5]``.
    """
    qc = QiskitCircuit(3)
    qc.h(0)
    qc.cx(0, 2)  # non-adjacent -> routed + angle-wrapped
    qc.rx(-1.7, 1)  # negative angle -> exercises RewriteRxAsR
    qc.measure_all()

    out = transpile(qc, "aqt")
    assert out.number_of_qubits == 3

    ops = out.quantum_circuit.root
    assert type(ops[-1].root).__name__ == "Measure"
    for op in ops:
        gate = op.root
        if type(gate).__name__ == "GateR":
            assert 0 <= gate.theta <= 1
        if type(gate).__name__ == "GateRXX":
            assert 0 <= gate.theta <= 0.5

    QuantumCircuit.model_validate(out.model_dump())


# ---------------------------------------------------------------------------
# ported qiskit passes
# ---------------------------------------------------------------------------


def test_rewrite_rx_as_r_positive_angle():
    """``Rx(theta)`` with theta >= 0 becomes ``R(theta, phi=0)``."""
    instruction = rewrite_rx_as_r(0.5)
    theta, phi = (float(p) for p in instruction.params)
    assert theta == pytest.approx(0.5)
    assert phi == pytest.approx(0.0)


def test_rewrite_rx_as_r_negative_angle():
    """A negative ``Rx`` angle is folded to a positive theta with ``phi = pi``."""
    instruction = rewrite_rx_as_r(-0.5)
    theta, phi = (float(p) for p in instruction.params)
    assert theta == pytest.approx(0.5)
    assert phi == pytest.approx(math.pi)


@pytest.mark.parametrize(
    "theta",
    [
        0.3,  # fast path |theta| <= pi/2
        -0.3,  # fast path, negative -> RZ-sandwiched RXX
        math.pi,  # |theta| in (pi/2, 3pi/2] branch
        -math.pi,  # same branch, negative sign
        1.9 * math.pi,  # |theta| > 3pi/2 branch after mod
        -1.9 * math.pi,  # same branch, negative sign
    ],
)
def test_wrap_rxx_angle_covers_all_branches(theta):
    """``wrap_rxx_angle`` returns a composite ``Rxx-wrapped`` instruction for every angle regime."""
    instruction = wrap_rxx_angle(theta)
    assert instruction.name.startswith("Rxx-wrapped")


def test_wrap_rxx_angles_pass_substitutes_out_of_range_gate():
    """The ``WrapRxxAngles`` pass substitutes an out-of-range ``rxx`` with a wrapped composite."""
    qc = QiskitCircuit(2)
    qc.rxx(3.0, 0, 1)  # 3.0 > pi/2 -> out of range, triggers substitution

    out = dag_to_circuit(WrapRxxAngles().run(circuit_to_dag(qc)))
    op_names = [instruction.operation.name for instruction in out.data]
    assert any(name.startswith("Rxx-wrapped") for name in op_names)


def test_wrap_rxx_angles_pass_leaves_in_range_gate_untouched():
    """An ``rxx`` already in ``[0, pi/2]`` is left unchanged by the pass."""
    qc = QiskitCircuit(2)
    qc.rxx(0.3, 0, 1)  # in range -> untouched

    out = dag_to_circuit(WrapRxxAngles().run(circuit_to_dag(qc)))
    op_names = [instruction.operation.name for instruction in out.data]
    assert op_names == ["rxx"]


def test_qiskit_to_aqt_circuit_requires_measurement():
    """A circuit without a measurement is rejected."""
    qc = QiskitCircuit(1)
    qc.rz(0.5, 0)
    with pytest.raises(ValueError, match="at least one measurement"):
        _qiskit_to_aqt_circuit(qc)


def test_qiskit_to_aqt_circuit_rejects_non_basis_gate():
    """A gate outside ``{rz, r, rxx}`` (plus measure/barrier) is rejected."""
    qc = QiskitCircuit(1)
    qc.x(0)
    qc.measure_all()
    with pytest.raises(ValueError, match="not in basis gate set"):
        _qiskit_to_aqt_circuit(qc)


def test_qiskit_to_aqt_circuit_rejects_mid_circuit_measurement():
    """A gate after a measurement is rejected (measurements must be terminal)."""
    qc = QiskitCircuit(1, 1)
    qc.rz(0.5, 0)
    qc.measure(0, 0)
    qc.rz(0.5, 0)
    with pytest.raises(ValueError, match="end of the circuit"):
        _qiskit_to_aqt_circuit(qc)


# ---------------------------------------------------------------------------
# program-type registration
# ---------------------------------------------------------------------------


def test_aqt_alias_registered_to_native_type():
    """The aqt_connector native circuit is registered under the ``aqt`` transpiler alias."""
    assert "aqt" in QPROGRAM_ALIASES
    assert QPROGRAM_REGISTRY["aqt"] is QuantumCircuit


def test_get_program_type_alias_for_native_circuit():
    """A native ``aqt_connector`` circuit resolves to the ``aqt`` alias."""
    assert get_program_type_alias(_aqt_quantum_circuit()) == "aqt"


@pytest.mark.parametrize("value", [{}, "not-a-circuit", 42, [1, 2, 3]])
def test_non_aqt_values_do_not_resolve_to_aqt(value):
    """Dicts, strings, ints, and lists do not resolve to the ``aqt`` alias."""
    assert get_program_type_alias(value, safe=True) != "aqt"


def test_qiskit_circuit_does_not_resolve_to_aqt():
    """A qiskit circuit resolves to ``qiskit``, not ``aqt``."""
    assert get_program_type_alias(QiskitCircuit(1)) == "qiskit"


# ---------------------------------------------------------------------------
# AQTProgram
# ---------------------------------------------------------------------------


def test_aqt_program_qubit_and_bit_counts():
    """``AQTProgram`` exposes qubits/num_qubits from the wrapped circuit and zero classical bits."""
    program = AQTProgram(_aqt_quantum_circuit(number_of_qubits=3))
    assert program.qubits == [0, 1, 2]
    assert program.num_qubits == 3
    assert program.num_clbits == 0


def test_aqt_program_serialize_not_implemented():
    """Like ``QiskitCircuit``, ``AQTProgram`` does not implement ``serialize``."""
    program = AQTProgram(_aqt_quantum_circuit())
    with pytest.raises(NotImplementedError):
        program.serialize()


@pytest.mark.parametrize("bad", [{"a": 1}, "circuit", 3.14])
def test_aqt_program_wrong_type_raises(bad):
    """Constructing ``AQTProgram`` with a non-AQT program raises ``ProgramTypeError``."""
    with pytest.raises(ProgramTypeError):
        AQTProgram(bad)


# ---------------------------------------------------------------------------
# sample -> counts
# ---------------------------------------------------------------------------


def test_samples_to_counts_reverses_each_sample():
    """Each per-shot sample is reversed to qBraid little-endian: ``[[1, 0]] -> {"01": 1}``."""
    assert _samples_to_counts({0: [[1, 0]]}) == {"01": 1}


def test_samples_to_counts_single_circuit_aggregates():
    """Repeated samples within a single circuit aggregate into counts (reversed bitstrings)."""
    counts = _samples_to_counts({0: [[1, 0, 1], [1, 0, 1], [0, 0, 0]]})
    assert counts == {"101": 2, "000": 1}


def test_samples_to_counts_batch_returns_list_in_index_order():
    """A multi-circuit result returns a list of per-circuit counts ordered by circuit index."""
    counts = _samples_to_counts({0: [[0, 1]], 1: [[1, 0], [1, 0]]})
    assert counts == [{"10": 1}, {"01": 2}]


# ---------------------------------------------------------------------------
# provider
# ---------------------------------------------------------------------------


def test_build_profile_targets_aqt_alias():
    """The profile's ``ProgramSpec`` targets the ``aqt`` alias, with arnica routing extras."""
    profile = AQTProvider._build_profile(
        {"id": "ibex", "type": "device", "available_qubits": 12}, "aqt"
    )
    assert profile.device_id == "aqt/ibex"
    assert profile.simulator is False
    assert profile.num_qubits == 12
    assert profile.provider_name == "AQT"
    assert profile.get("aqt_workspace_id") == "aqt"
    assert profile.get("aqt_resource_id") == "ibex"
    assert profile.get("aqt_resource_type") == "device"

    spec = profile.program_spec
    assert isinstance(spec, ProgramSpec)
    assert spec.alias == "aqt"


def test_get_devices():
    """``get_devices`` builds one ``AQTDevice`` per resource across visible workspaces."""
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


def test_get_device():
    """``get_device`` resolves a ``"<workspace>/<resource>"`` id to an ``AQTDevice``."""
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
    """A device id without a ``/`` separator raises ``ResourceNotFoundError``."""
    provider = AQTProvider(access_token="tok")
    with pytest.raises(ResourceNotFoundError):
        provider.get_device("no-separator")


def test_provider_hash():
    """``AQTProvider`` is hashable (keyed on token + base url)."""
    provider = AQTProvider(access_token="tok")
    assert isinstance(hash(provider), int)


# ---------------------------------------------------------------------------
# device: status
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,expected",
    [
        ("online", DeviceStatus.ONLINE),
        ("offline", DeviceStatus.OFFLINE),
        ("maintenance", DeviceStatus.UNAVAILABLE),
        ("unavailable", DeviceStatus.UNAVAILABLE),
    ],
)
def test_device_status_mapping(device, mock_session, status, expected):
    """The arnica resource status is mapped to the qBraid ``DeviceStatus``."""
    mock_session.get_resource.return_value = {"status": status}
    assert device.status() == expected


def test_device_status_unknown_raises(device, mock_session):
    """An unrecognized status raises ``ValueError``."""
    mock_session.get_resource.return_value = {"status": "banana"}
    with pytest.raises(ValueError):
        device.status()


def test_device_str(device):
    """``str(device)`` renders the device id."""
    assert str(device) == "AQTDevice('default/sim1')"


# ---------------------------------------------------------------------------
# device: submit
# ---------------------------------------------------------------------------


def test_device_submit_single_body_shape(device, mock_session):
    """A single native circuit is submitted with ``repetitions=shots`` and ``name`` as the label."""
    circuit = _aqt_quantum_circuit(number_of_qubits=2)
    job = device.submit(circuit, shots=250, name="demo")

    assert isinstance(job, AQTJob)
    assert job.id == "job-1"

    mock_session.submit_job.assert_called_once()
    ws, res, body = mock_session.submit_job.call_args.args
    assert (ws, res) == ("default", "sim1")
    assert body["job_type"] == "quantum_circuit"
    assert body["label"] == "demo"

    circuits = body["payload"]["circuits"]
    assert len(circuits) == 1
    assert circuits[0]["repetitions"] == 250
    assert circuits[0]["number_of_qubits"] == 2


def test_device_submit_default_label(device, mock_session):
    """When ``name`` is omitted, the job label defaults to ``"qbraid"``."""
    device.submit(_aqt_quantum_circuit(), shots=10)
    _ws, _res, body = mock_session.submit_job.call_args.args
    assert body["label"] == "qbraid"


def test_device_submit_batch(device, mock_session):
    """A list of circuits is submitted as a single batch with per-circuit ``repetitions=shots``."""
    circuits = [_aqt_quantum_circuit(2), _aqt_quantum_circuit(2)]
    device.submit(circuits, shots=64)

    _ws, _res, body = mock_session.submit_job.call_args.args
    payload_circuits = body["payload"]["circuits"]
    assert len(payload_circuits) == 2
    assert all(c["repetitions"] == 64 for c in payload_circuits)


def test_device_submit_missing_job_id_raises(device, mock_session):
    """A submission response without a ``job_id`` raises ``ValueError``."""
    mock_session.submit_job.return_value = {"job": {}}
    with pytest.raises(ValueError):
        device.submit(_aqt_quantum_circuit())


def test_device_run_end_to_end(device, mock_session):
    """``run`` transpiles a qiskit circuit through the ``qiskit -> aqt`` edge, then submits it."""
    # ``run`` -> validate -> status() -> get_resource must report online.
    mock_session.get_resource.return_value = {"status": "online"}

    qc = QiskitCircuit(2)
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


# ---------------------------------------------------------------------------
# job: status
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,expected",
    [
        ("queued", JobStatus.QUEUED),
        ("ongoing", JobStatus.RUNNING),
        ("finished", JobStatus.COMPLETED),
        ("cancelled", JobStatus.CANCELLED),
    ],
)
def test_job_status_mapping(mock_session, status, expected):
    """Each arnica job status maps to the corresponding qBraid ``JobStatus``."""
    result = {"0": [[1, 0]]} if status == "finished" else None
    mock_session.get_result.return_value = _result_payload(status, result=result)
    job = AQTJob("job-1", session=mock_session)
    assert job.status() == expected


def test_job_status_error_state(mock_session):
    """An error response maps to ``JobStatus.FAILED``."""
    mock_session.get_result.return_value = _result_payload("error", message="boom")
    job = AQTJob("job-1", session=mock_session)
    assert job.status() == JobStatus.FAILED


def test_job_cancel(mock_session):
    """``cancel`` delegates to ``session.cancel_job`` with the job id."""
    job = AQTJob("job-1", session=mock_session)
    job.cancel()
    mock_session.cancel_job.assert_called_once_with("job-1")


# ---------------------------------------------------------------------------
# job: execution time
# ---------------------------------------------------------------------------


def test_execution_time_s_from_timing_data(mock_session):
    """execution_time_s is the ongoing -> finished span of the arnica timing_data, in seconds."""
    mock_session.get_result.return_value = {
        "job": {
            "job_id": "00000000-0000-0000-0000-0000000000ab",
            "workspace_id": "ws",
            "resource_id": "res",
        },
        "response": {
            "status": "finished",
            "timing_data": [
                {"new_status": "queued", "timestamp": "2026-07-16T10:21:41.435142Z"},
                {"new_status": "ongoing", "timestamp": "2026-07-16T10:21:41.939164Z"},
                {"new_status": "finished", "timestamp": "2026-07-16T10:21:42.032645Z"},
            ],
            "result": {"0": [[1, 1, 1]]},
        },
    }
    job = AQTJob("00000000-0000-0000-0000-0000000000ab", session=mock_session)
    assert job.execution_time_s() == pytest.approx(0.093481)
    assert mock_session.get_result.call_args.kwargs == {"include_timing_data": True}


def test_execution_time_s_none_when_not_completed(mock_session):
    """execution_time_s returns None for a job that has not finished."""
    mock_session.get_result.return_value = _result_payload("ongoing")
    job = AQTJob("job-1", session=mock_session)
    assert job.execution_time_s() is None


def test_execution_time_s_raises_when_finished_without_timing(mock_session):
    """A finished job missing timing_data raises ``AQTJobError`` rather than returning None."""
    mock_session.get_result.return_value = _result_payload("finished", result={"0": [[1]]})
    job = AQTJob("job-1", session=mock_session)
    with pytest.raises(AQTJobError):
        job.execution_time_s()


# ---------------------------------------------------------------------------
# job: result
# ---------------------------------------------------------------------------


def test_job_result_success_reversed_counts(device, mock_session):
    """A finished job yields a successful ``Result`` with reversed (little-endian) counts."""
    mock_session.get_result.return_value = _result_payload(
        "finished",
        result={"0": [[1, 0], [1, 0], [0, 1]]},
        workspace_id="default",
        resource_id="sim1",
    )
    job = AQTJob("job-1", session=mock_session, device=device)
    result = job.result()
    assert result.success is True
    # [1, 0] -> "01", [0, 1] -> "10"
    assert result.data.get_counts() == {"01": 2, "10": 1}


def test_job_result_error_raises_aqt_job_error(mock_session):
    """A non-finished (error) response raises ``AQTJobError`` carrying the arnica message."""
    mock_session.get_result.return_value = _result_payload("error", message="calibration drift")
    job = AQTJob("job-1", session=mock_session)
    with pytest.raises(AQTJobError, match="calibration drift"):
        job.result()


def test_job_result_device_id_from_metadata(mock_session):
    """With no attached device, the result device id is derived from arnica job metadata."""
    mock_session.get_result.return_value = _result_payload(
        "finished", result={"0": [[0], [1]]}, workspace_id="ws", resource_id="res"
    )
    result = AQTJob("job-1", session=mock_session).result()
    assert result.device_id == "ws/res"


def test_job_session_none_fallback(monkeypatch):
    """``AQTJob(session=None)`` lazily builds a default ``AQTSession``."""
    sentinel = MagicMock(name="AQTSession()")
    monkeypatch.setattr("qbraid.runtime.aqt.provider.AQTSession", lambda: sentinel)
    assert AQTJob("job-1").session is sentinel


# ---------------------------------------------------------------------------
# AQTSession HTTP
# ---------------------------------------------------------------------------


def _mock_http_session() -> AQTSession:
    """A real ``AQTSession`` with its ``requests`` transport (get/post/delete) mocked out."""
    session = AQTSession(access_token="tok")
    session.get = MagicMock()
    session.post = MagicMock()
    session.delete = MagicMock()
    return session


def test_session_base_url_and_token():
    """The base url appends ``/v1`` to the arnica root, and the token is exposed."""
    session = AQTSession(access_token="tok", arnica_url="https://example.test/api")
    assert session.base_url == "https://example.test/api/v1"
    assert session.access_token == "tok"


def test_session_base_url_strips_duplicate_v1():
    """A URL already ending in ``/v1`` is normalized rather than doubled."""
    session = AQTSession(access_token="tok", arnica_url="https://example.test/api/v1")
    assert session.base_url == "https://example.test/api/v1"


def test_session_explicit_token_skips_resolution(monkeypatch):
    """An explicit ``access_token`` short-circuits ``_resolve_access_token`` entirely."""

    def _fail(*_args, **_kwargs):
        raise AssertionError("_resolve_access_token should not be called for an explicit token")

    monkeypatch.setattr("qbraid.runtime.aqt.provider._resolve_access_token", _fail)
    session = AQTSession(access_token="explicit-token")
    assert session.access_token == "explicit-token"


def test_session_http_methods():
    """Each session helper hits the right route and returns the decoded JSON body."""
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


def _requests_api_error(status_code: int) -> RequestsApiError:
    """A ``RequestsApiError`` chained from an ``HTTPError`` whose response carries a status code."""
    cause = requests.HTTPError("http error")
    cause.response = types.SimpleNamespace(status_code=status_code)
    error = RequestsApiError("request failed")
    error.__cause__ = cause
    return error


def test_session_get_resource_404_maps_to_not_found():
    """A genuine 404 from arnica is surfaced as ``ResourceNotFoundError``."""
    session = _mock_http_session()
    session.get.side_effect = _requests_api_error(404)
    with pytest.raises(ResourceNotFoundError):
        session.get_resource("missing")


def test_session_get_resource_non_404_propagates():
    """A non-404 (e.g. 401 auth) ``RequestsApiError`` propagates instead of mapping to not-found."""
    session = _mock_http_session()
    session.get.side_effect = _requests_api_error(401)
    with pytest.raises(RequestsApiError):
        session.get_resource("forbidden")


# ---------------------------------------------------------------------------
# auth resolution
# ---------------------------------------------------------------------------


class _FakeArnicaConfig:
    """Stand-in for ``aqt_connector.ArnicaConfig`` mirroring the fields the resolver touches."""

    def __init__(self) -> None:
        self.client_id = None
        self.client_secret = None
        self.store_access_token = True
        # Mirror the real defaults: audience/arnica_url point at production.
        self.arnica_url = "https://arnica.aqt.eu/api"
        self.oidc_config = types.SimpleNamespace(audience="https://arnica.aqt.eu/api")


def _patch_arnica(monkeypatch, *, stored=None, cc_token="cc-token") -> dict[str, Any]:
    """Monkeypatch the real ``aqt_connector`` auth functions on the provider module.

    Returns a dict whose ``"config"`` key is populated with the ``ArnicaConfig`` passed to
    ``ArnicaApp`` once ``_resolve_access_token`` runs.
    """
    captured: dict[str, Any] = {"config": None}

    def fake_arnica_app(config):
        captured["config"] = config
        return types.SimpleNamespace(config=config)

    monkeypatch.setattr("qbraid.runtime.aqt.provider.ArnicaConfig", _FakeArnicaConfig)
    monkeypatch.setattr("qbraid.runtime.aqt.provider.ArnicaApp", fake_arnica_app)
    monkeypatch.setattr("qbraid.runtime.aqt.provider.get_access_token", lambda app: stored)
    monkeypatch.setattr("qbraid.runtime.aqt.provider.log_in", lambda app: cc_token)
    return captured


def test_resolve_token_stored_session(monkeypatch):
    """A stored/refreshed aqt-connector session token is returned when present."""
    monkeypatch.delenv("AQT_CLIENT_ID", raising=False)
    monkeypatch.delenv("AQT_CLIENT_SECRET", raising=False)
    _patch_arnica(monkeypatch, stored="stored")
    assert _resolve_access_token() == "stored"


def test_resolve_token_client_credentials_from_env(monkeypatch):
    """With no stored token, ``AQT_CLIENT_ID``/``AQT_CLIENT_SECRET`` drive the client-credentials
    flow."""
    monkeypatch.setenv("AQT_CLIENT_ID", "cid")
    monkeypatch.setenv("AQT_CLIENT_SECRET", "csecret")
    captured = _patch_arnica(monkeypatch, stored=None, cc_token="cc")

    assert _resolve_access_token() == "cc"
    assert captured["config"].client_id == "cid"
    assert captured["config"].client_secret == "csecret"


def test_resolve_token_disables_persistence(monkeypatch):
    """The resolver disables token persistence (``store_access_token = False``)."""
    monkeypatch.setenv("AQT_CLIENT_ID", "cid")
    monkeypatch.setenv("AQT_CLIENT_SECRET", "csecret")
    captured = _patch_arnica(monkeypatch, stored=None, cc_token="cc")

    _resolve_access_token()
    assert captured["config"].store_access_token is False


def test_resolve_token_applies_audience(monkeypatch):
    """A non-default audience (e.g. staging) is applied to both the request and the verifier."""
    monkeypatch.setenv("AQT_CLIENT_ID", "cid")
    monkeypatch.setenv("AQT_CLIENT_SECRET", "csecret")
    captured = _patch_arnica(monkeypatch, stored=None, cc_token="cc")

    staging = "https://arnica-staging.aqt.eu/api"
    assert _resolve_access_token(audience=staging) == "cc"
    assert captured["config"].arnica_url == staging
    assert captured["config"].oidc_config.audience == staging
    assert captured["config"].store_access_token is False


def test_resolve_token_none_available_raises(monkeypatch):
    """With no token and no client credentials, resolution raises ``ValueError``."""
    monkeypatch.delenv("AQT_CLIENT_ID", raising=False)
    monkeypatch.delenv("AQT_CLIENT_SECRET", raising=False)
    _patch_arnica(monkeypatch, stored=None)
    with pytest.raises(ValueError, match="No AQT access token"):
        _resolve_access_token()

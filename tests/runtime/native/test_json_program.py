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


"""
Unit tests for submitting JSON programs, such as qBraid OS ``pulse.schedule.v1``, to native
devices.

"""
import threading
from unittest.mock import MagicMock

import numpy as np
import pytest
from qbraid_core.services.runtime import schemas
from qbraid_core.services.runtime.schemas import BatchResult as CoreBatchResult
from qbraid_core.services.runtime.schemas import Program
from qbraid_core.services.runtime.schemas import Result as CoreResult
from qbraid_core.services.runtime.schemas import RuntimeDevice, RuntimeJob

from qbraid.programs import (
    QPROGRAM_REGISTRY,
    get_program_type_alias,
    register_program_type,
    unregister_program_type,
)
from qbraid.programs.registry import register_json_program_type
from qbraid.programs.typer import (
    _FALLBACK_JSON_PROGRAM_TYPE_PATTERN,
    _FALLBACK_RESERVED_PROGRAM_TYPE_PREFIXES,
    is_json_program_type,
    json_program_type_rules,
)
from qbraid.runtime import DeviceStatus
from qbraid.runtime.exceptions import ProgramValidationError
from qbraid.runtime.native import QbraidDevice, QbraidJob, QbraidProvider
from qbraid.runtime.native.provider import get_program_spec_lambdas
from qbraid.transpiler import ProgramConversionError

# Until the SDK requires it: qbraid-core 0.6.55 is the first to accept JSON program formats.
requires_json_formats = pytest.mark.skipif(
    not hasattr(schemas, "is_json_program_type"),
    reason="the installed qbraid-core does not accept JSON program formats",
)

QRN = "qbraid_os:0123456789abcdef01234567:qpu:lab-1.lab-transmon"
JSON_TYPES = ["pulse.schedule.v1", "calibration.v1", "ahs.v1", "acme.iq_trace.v1"]

# A device as qBraid OS registers it in qbraid-api (qbraid-os ``Store.registration_body``).
DEVICE_DATA = {
    "name": "lab-1.lab-transmon",
    "qrn": QRN,
    "vendor": "qbraid_os",
    "deviceType": "QPU",
    "runInputTypes": ["qasm3", "qasm2", *JSON_TYPES],
    "status": "ONLINE",
    "numberQubits": 2,
    "paradigm": "gate_model",
    "visibility": "private",
    "pricing": None,
}

PULSE = {
    "type": "pulse.schedule.v1",
    "instructions": [
        {"op": "play", "channel": "d0", "amp": 0.21, "durationNs": 40, "sigmaNs": 10},
        {"op": "acquire", "qubits": [0]},
    ],
}

BELL = """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
c = measure q;
"""


@pytest.fixture(autouse=True)
def _restore_registry():
    """Drop the JSON program types a test registered, so other tests see the usual registry."""
    before = set(QPROGRAM_REGISTRY)
    yield
    for alias in set(QPROGRAM_REGISTRY) - before:
        unregister_program_type(alias, raise_error=False)


class _Submitted(Exception):
    """Raised by the mock client to stop after the job request is built."""


def _device(run_input_types: list[str] | None = None, **fields) -> tuple[QbraidDevice, MagicMock]:
    client = MagicMock()
    client.create_job.side_effect = _Submitted
    data = {**DEVICE_DATA, **fields}
    if run_input_types is not None:
        data["runInputTypes"] = run_input_types
    profile = QbraidProvider(client=client)._build_runtime_profile(RuntimeDevice(**data))
    device = QbraidDevice(profile, client=client)
    device.status = MagicMock(return_value=DeviceStatus.ONLINE)
    return device, client


@pytest.mark.parametrize(
    "alias, expected",
    [
        ("pulse.schedule.v1", True),
        ("calibration.v1", True),
        ("ahs.v1", True),
        ("acme.iq_trace.v1", True),
        ("foo.v1", True),
        ("a" * 32 + "." + "b" * 40 + ".v1234", True),  # at every length cap
        ("ionq.circuit.v0", False),  # IonQ's own format, with its own rules
        ("qir.v1", False),  # reserved vendor prefixes: existing vendor format strings
        ("ionq.circuit.v1", False),
        ("honeywell.openqasm.v1", False),
        ("rigetti.quil.v1", False),
        ("pasqal.pulser.v1", False),
        ("acme.qiskit_trace.v1", True),  # only the first segment is reserved
        ("qasm3", False),
        ("pulser", False),
        ("foo", False),
        ("1abc.v1", False),
        ("a.b.c.v1", False),
        ("a" * 33 + ".b.v1", False),
        ("acme." + "b" * 41 + ".v1", False),
        ("acme.b.v12345", False),
        ("acme_x.b.v1", False),
        ("Acme.iq_trace.v1", False),
        ("pulse.schedule.v1\n", False),
        (None, False),
    ],
)
def test_is_json_program_type(alias, expected):
    """JSON program types are ``<name>.v<N>`` or ``<vendor>.<name>.v<N>``, within length caps."""
    assert is_json_program_type(alias) is expected


def test_rules_come_from_qbraid_core_when_it_has_them():
    """The pattern and reserved prefixes are qbraid-core's; the copies match them."""
    pattern, reserved = json_program_type_rules()
    assert pattern.pattern == _FALLBACK_JSON_PROGRAM_TYPE_PATTERN.pattern
    assert reserved == _FALLBACK_RESERVED_PROGRAM_TYPE_PREFIXES
    if hasattr(schemas, "JSON_PROGRAM_TYPE_PATTERN"):
        assert pattern is schemas.JSON_PROGRAM_TYPE_PATTERN
        assert reserved == schemas.RESERVED_PROGRAM_TYPE_PREFIXES


def test_json_program_type_matches_dicts_by_type():
    """The marker class matches a dict by its "type" and is the same class on each call."""
    marker = register_json_program_type("pulse.schedule.v1")
    assert marker is register_json_program_type("pulse.schedule.v1")
    assert QPROGRAM_REGISTRY["pulse.schedule.v1"] is marker
    assert isinstance(PULSE, marker)
    assert not isinstance({**PULSE, "type": "calibration.v1"}, marker)
    assert not isinstance("pulse.schedule.v1", marker)
    with pytest.raises(ValueError, match="not a JSON program type"):
        register_json_program_type("qasm3")


def test_profile_lists_json_types_after_the_gate_formats():
    """A qBraid OS device's profile offers each run input type, JSON types included."""
    device, _ = _device()
    assert [spec.alias for spec in device.profile.program_spec] == DEVICE_DATA["runInputTypes"]
    assert get_program_type_alias(PULSE) == "pulse.schedule.v1"


@requires_json_formats
@pytest.mark.parametrize("program_type", JSON_TYPES)
def test_json_program_serializes_as_written(program_type):
    """The serializer sends the dict unchanged, with its type as the format."""
    program = {"type": program_type, "payload": {"samples": [0.0, 0.5]}}
    serialize = get_program_spec_lambdas(program_type, QRN)["serialize"]
    wrapped = serialize(program)
    assert wrapped == Program(format=program_type, data=program)
    assert wrapped.data is program


@requires_json_formats
def test_run_submits_pulse_program_untranspiled():
    """run() sends a pulse schedule as a 'pulse.schedule.v1' Program, without a transform."""
    device, client = _device()

    with pytest.raises(_Submitted):
        device.run(PULSE, shots=100)

    request = client.create_job.call_args.args[0]
    assert request.program == Program(format="pulse.schedule.v1", data=PULSE)
    assert request.metadata == {"programType": "pulse.schedule.v1"}
    body = request.model_dump(exclude={"metadata"})
    assert body["program"] == {"format": "pulse.schedule.v1", "data": PULSE}
    assert body["deviceQrn"] == QRN and body["shots"] == 100


@requires_json_formats
@pytest.mark.parametrize("program_type", ["calibration.v1", "ahs.v1", "acme.iq_trace.v1"])
def test_submit_accepts_a_json_program_dict(program_type):
    """submit() wraps a JSON program dict itself."""
    device, client = _device()
    program = {"type": program_type, "experiment": "rabi", "qubit": 0}

    with pytest.raises(_Submitted):
        device.submit(program, shots=10)

    request = client.create_job.call_args.args[0]
    assert request.program == Program(format=program_type, data=program)


@requires_json_formats
def test_submit_batch_of_json_programs():
    """A batch of JSON programs goes as one request holding each program."""
    device, client = _device(batchJobSupport=True)
    second = {**PULSE, "instructions": PULSE["instructions"][1:]}

    with pytest.raises(_Submitted):
        device.submit([PULSE, second], shots=10, as_batch=True)

    request = client.create_job.call_args.args[0]
    assert request.program == [
        Program(format="pulse.schedule.v1", data=PULSE),
        Program(format="pulse.schedule.v1", data=second),
    ]


@pytest.mark.parametrize("method", ["run", "submit"])
def test_device_without_the_type_refuses_it(method):
    """A device whose profile lacks the type refuses the program before any request."""
    device, client = _device(["qasm3", "qasm2", "calibration.v1"])

    with pytest.raises(ProgramValidationError, match="does not accept 'pulse.schedule.v1'"):
        getattr(device, method)(PULSE, shots=10)
    client.create_job.assert_not_called()


def test_gate_only_device_refuses_json_program():
    """A gate-only device refuses a JSON program, naming the types it accepts."""
    device, client = _device(["qasm3", "qasm2"])

    with pytest.raises(ProgramValidationError, match="Accepted program types: qasm2, qasm3"):
        device.run(PULSE, shots=10)
    client.create_job.assert_not_called()


@pytest.mark.skipif(
    hasattr(schemas, "is_json_program_type"), reason="the installed qbraid-core accepts them"
)
def test_old_qbraid_core_names_the_version_needed():
    """With a qbraid-core that predates JSON formats, the error says which version is needed."""
    device, client = _device()

    with pytest.raises(ProgramValidationError, match="requires qbraid-core 0.6.55"):
        device.submit(PULSE, shots=10)
    client.create_job.assert_not_called()


def test_gate_circuit_still_converts_to_qasm3():
    """A circuit on a qBraid OS device is converted to qasm3 as before."""
    qiskit = pytest.importorskip("qiskit")
    circuit = qiskit.QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure_all()
    device, client = _device()

    with pytest.raises(_Submitted):
        device.run(circuit, shots=10)

    request = client.create_job.call_args.args[0]
    assert request.program.format == "qasm3"
    assert request.program.data.startswith("OPENQASM 3.0;")
    assert request.metadata == {"programType": "qiskit"}


def test_qasm_string_still_sent_as_qasm3():
    """An OpenQASM 3 string goes to a qBraid OS device as a qasm3 Program."""
    device, client = _device()

    with pytest.raises(_Submitted):
        device.run(BELL, shots=10)

    request = client.create_job.call_args.args[0]
    assert request.program.format == "qasm3"
    assert "cx q[0], q[1];" in request.program.data


def test_other_dicts_are_not_json_programs():
    """A dict without a JSON program type is left to the usual program checks."""
    device, client = _device()

    with pytest.raises(ProgramConversionError, match="No conversion path found from 'dict'"):
        device.run({"type": "qasm3", "instructions": []}, shots=10)
    client.create_job.assert_not_called()


def test_non_json_run_input_types_unchanged():
    """Devices without JSON run input types get the same specs as before."""
    specs = QbraidProvider._get_program_specs(["qasm3", "qasm2", "ionq.circuit.v0"], QRN)
    assert [spec.alias for spec in specs] == ["qasm3", "qasm2"]


def test_concurrent_profile_builds_register_one_marker():
    """Threads building specs for the same new type all get the one registered marker."""
    for i in range(50):
        alias = f"race{i}.v1"
        barrier = threading.Barrier(8)
        errors: list[Exception] = []
        specs: list = []

        def work(
            alias: str, barrier: threading.Barrier, errors: list[Exception], specs: list
        ) -> None:
            barrier.wait()
            try:
                specs.append(QbraidProvider._get_program_spec(alias, QRN))
            except Exception as err:  # pylint: disable=broad-exception-caught
                errors.append(err)

        threads = [
            threading.Thread(target=work, args=(alias, barrier, errors, specs)) for _ in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert not errors
        assert len({spec.program_type for spec in specs}) == 1
        assert specs[0].program_type is QPROGRAM_REGISTRY[alias]


IONQ_SHAPED = {
    "type": "acme.circuit.v1",
    "qubits": 2,
    "circuit": [{"gate": "h", "target": 0}, {"gate": "cnot", "control": 0, "target": 1}],
}


def _sent(device, client, method, program):
    client.reset_mock()
    with pytest.raises(_Submitted):
        getattr(device, method)(program, shots=10)
    return client.create_job.call_args.args[0]


@requires_json_formats
@pytest.mark.parametrize("run_input_types", [["qasm3", "acme.circuit.v1"], ["acme.circuit.v1"]])
def test_ionq_shaped_json_program_is_not_ionq(run_input_types):
    """A JSON program shaped like IonQ JSON keeps its own type, and run() matches submit()."""
    device, client = _device(run_input_types)
    assert get_program_type_alias(IONQ_SHAPED) == "acme.circuit.v1"

    via_run = _sent(device, client, "run", IONQ_SHAPED)
    via_submit = _sent(device, client, "submit", IONQ_SHAPED)
    assert via_run.program == Program(format="acme.circuit.v1", data=IONQ_SHAPED)
    assert via_run.model_dump() == via_submit.model_dump()
    assert via_run.metadata == {"programType": "acme.circuit.v1"}


@requires_json_formats
@pytest.mark.parametrize("program", [PULSE, {"type": "calibration.v1", "routine": "rabi"}])
def test_run_and_submit_send_the_same_request(program):
    """run() and submit() send identical requests for a JSON program."""
    device, client = _device()
    assert (
        _sent(device, client, "run", program).model_dump()
        == _sent(device, client, "submit", program).model_dump()
    )


@requires_json_formats
def test_json_program_with_users_own_dict_type():
    """A dict type the user registered does not stop JSON programs."""
    register_program_type(dict, alias="mydict")
    device, client = _device()
    assert get_program_type_alias({"a": 1}) == "mydict"
    assert get_program_type_alias(PULSE) == "pulse.schedule.v1"

    for method in ("run", "submit"):
        request = _sent(device, client, method, PULSE)
        assert request.program == Program(format="pulse.schedule.v1", data=PULSE)


@requires_json_formats
def test_mixed_run_converts_circuits_and_sends_json_as_written():
    """A run() list of a QASM circuit and a JSON program handles each the right way."""
    device, client = _device()
    client.create_job.side_effect = None
    client.create_job.return_value = MagicMock(jobQrn="qbraid_os:lab-1.lab-transmon-job-1")

    device.run([BELL, PULSE], shots=10)

    circuit, pulse = (call.args[0] for call in client.create_job.call_args_list)
    assert circuit.program.format == "qasm3"
    assert circuit.metadata == {"programType": "qasm3"}
    assert pulse.program == Program(format="pulse.schedule.v1", data=PULSE)
    assert pulse.metadata == {"programType": "pulse.schedule.v1"}


def test_target_spec_narrowed_by_user_refuses_json():
    """The device check reads the targeted specs, so a narrowed target refuses JSON programs."""
    device, client = _device()
    device.set_target_program_type("qasm3")

    for method in ("run", "submit"):
        with pytest.raises(ProgramValidationError, match="Accepted program types: qasm3"):
            getattr(device, method)(PULSE, shots=10)
    client.create_job.assert_not_called()


@pytest.mark.parametrize(
    "program, reason",
    [
        ({"type": "pulse.schedule.v1", "samples": np.array([0.1, 0.2])}, "ndarray"),
        ({"type": "pulse.schedule.v1", "amp": 0.2 + 0.1j}, "complex"),
        ({"type": "pulse.schedule.v1", "amp": float("nan")}, "nan"),
        ({"type": "pulse.schedule.v1", "amp": float("inf")}, "inf"),
        ({"type": "pulse.schedule.v1", ("a", "b"): 1}, "keys must be"),
    ],
)
@pytest.mark.parametrize("method", ["run", "submit"])
def test_non_json_values_are_refused(program, reason, method):
    """A program that is not plain JSON is refused before any request, naming the problem."""
    device, client = _device()

    with pytest.raises(ProgramValidationError, match="not valid JSON") as exc:
        getattr(device, method)(program, shots=10)
    assert reason in str(exc.value)
    client.create_job.assert_not_called()


@requires_json_formats
def test_numpy_scalars_that_are_floats_are_accepted():
    """A NumPy float64 is a float, so it serializes as JSON and is accepted."""
    device, client = _device()
    program = {"type": "pulse.schedule.v1", "amp": np.float64(0.2)}
    request = _sent(device, client, "run", program)
    assert request.model_dump(mode="json")["program"]["data"] == {
        "type": "pulse.schedule.v1",
        "amp": 0.2,
    }


# Results as the qBraid OS transmon connector returns them (qbraid_os/connectors/transmon.py,
# from a run of the emulated device), after qbraid-runtime-api stores "counts" as
# "measurementCounts".
TIME_STAMPS = {
    "createdAt": "2026-11-15T04:02:14Z",
    "endedAt": "2026-11-15T04:02:15Z",
    "executionDuration": 1012,
}
PULSE_RESULT = {"measurementCounts": {"0": 6, "1": 94}, "acquired": [0], "calibrationVersion": 1}
RABI_RESULT = {
    "routine": "rabi",
    "qubit": 0,
    "amps": [0.0, 0.25, 0.5, 0.75, 1.0],
    "p1": [0.04, 0.52, 0.84, 0.1, 0.32],
    "fit": {"piAmp": 0.419},
    "previousPiAmp": 0.58,
    "applied": True,
    "calibrationUpdate": {
        "version": 2,
        "updatedAt": "2026-11-15T04:02:15Z",
        "updatedBy": "bob (rabi q0)",
        "driveFreqGHz": [5.1047, 5.3172],
        "piAmp": [0.419, 0.3],
        "pulse": {"shape": "gaussian", "durationNs": 40, "sigmaNs": 10},
    },
    "calibrationVersion": 2,
}
T1_RESULT = {
    "routine": "t1",
    "qubit": 0,
    "delaysNs": [0.0, 50000.0, 100000.0, 150000.0],
    "p1": [0.98, 0.22, 0.16, 0.02],
    "fit": {"t1Us": 30.72},
    "applied": False,
    "calibrationVersion": 2,
}


def _job(result_data):
    qrn = f"{QRN}-qjob-1"
    job_data = RuntimeJob(
        jobQrn=qrn,
        deviceQrn=QRN,
        status="COMPLETED",
        shots=100,
        numCircuits=1,
        # How qBraid OS registers pulse- and calibration-capable devices.
        experimentType="gate_model",
        cost=0,
        estimatedCost=0,
        vendor="qbraid_os",
        provider="qbraid_os",
        timeStamps=TIME_STAMPS,
    )
    client = MagicMock()
    client.get_job.return_value = job_data
    client.get_job_result.return_value = CoreResult(
        status="COMPLETED", cost=0, timeStamps=TIME_STAMPS, resultData=result_data
    )
    return QbraidJob(qrn, client=client)


def test_pulse_result_counts_and_extras():
    """A pulse schedule's counts read as counts; the connector's extras stay with them."""
    result = _job(PULSE_RESULT).result()
    assert result.success is True
    assert result.data.get_counts() == {"0": 6, "1": 94}
    assert result.data.extra == {"acquired": [0], "calibrationVersion": 1}
    assert result.details["calibrationVersion"] == 1


@pytest.mark.parametrize("raw", [RABI_RESULT, T1_RESULT])
def test_calibration_result_without_counts(raw):
    """A calibration result has no counts: result() works, and the routine output is readable."""
    job = _job(raw)
    result = job.result()
    assert result.success is True
    assert result.data.measurement_counts is None
    assert result.data.extra == raw
    assert result.details["fit"] == raw["fit"]
    assert repr(result) and str(result)
    with pytest.raises(ValueError, match="Counts data is not available"):
        result.data.get_counts()
    assert job.raw_result() == raw


@pytest.mark.parametrize(
    "raw",
    [
        {**RABI_RESULT, "status": "converged"},
        {"data": {"iq": [[0.1, 0.2]]}, "calibrationVersion": 2},
        {"cost": 3, "routine": "t1"},
        {"success": False, "device_id": "lab", "job_id": 7, "time_stamps": 0},
        {"status_message": "fit failed"},
    ],
)
def test_result_keys_named_like_result_fields(raw):
    """Device keys named like Result fields do not break result() or shadow its fields."""
    job = _job(raw)
    result = job.result()
    assert result.success is True
    assert result.data.extra == raw
    assert result.details["status"].name == "COMPLETED"
    assert result.details["cost"] == 0
    assert result.device_id == QRN
    assert (
        not set(raw)
        - set(result.details)
        - {
            "status",
            "data",
            "cost",
            "success",
            "device_id",
            "job_id",
            "time_stamps",
            "status_message",
        }
    )
    assert "status_message" not in result.details
    assert job.raw_result() == raw


def test_raw_result_of_a_batch_job():
    """raw_result() returns one dict per circuit of a batch job."""
    job = _job({})
    job.client.get_job_result.return_value = CoreBatchResult(
        status="COMPLETED",
        cost=0,
        timeStamps=TIME_STAMPS,
        results=[
            CoreResult(status="COMPLETED", cost=0, timeStamps=TIME_STAMPS, resultData=PULSE_RESULT),
            CoreResult(status="COMPLETED", cost=0, timeStamps=TIME_STAMPS, resultData=T1_RESULT),
        ],
    )
    assert job.raw_result() == [PULSE_RESULT, T1_RESULT]

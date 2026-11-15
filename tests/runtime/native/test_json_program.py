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
from unittest.mock import MagicMock

import pytest
from qbraid_core.services.runtime import schemas
from qbraid_core.services.runtime.schemas import Program, RuntimeDevice

from qbraid.programs import QPROGRAM_REGISTRY, get_program_type_alias, unregister_program_type
from qbraid.programs.typer import is_json_program_type, json_program_type
from qbraid.runtime import DeviceStatus
from qbraid.runtime.exceptions import ProgramValidationError
from qbraid.runtime.native import QbraidDevice, QbraidProvider
from qbraid.runtime.native.provider import get_program_spec_lambdas
from qbraid.transpiler import ProgramConversionError

# Until the SDK requires it: qbraid-core 0.6.55 is the first to accept JSON program formats.
requires_json_formats = pytest.mark.skipif(
    not hasattr(schemas, "is_json_program_type"),
    reason="the installed qbraid-core does not accept JSON program formats",
)

QRN = "qbraid_os:0123456789abcdef01234567:qpu:lab-1.lab-transmon"
JSON_TYPES = ["pulse.schedule.v1", "calibration.v1", "acme.iq_trace.v1"]

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
        ("ionq.circuit.v0", False),  # IonQ's own format, with its own rules
        ("qasm3", False),
        ("pulser", False),
        ("foo.v1", False),
        ("Acme.iq_trace.v1", False),
        (None, False),
    ],
)
def test_is_json_program_type(alias, expected):
    """The JSON program types are the named ones and ``<vendor>.<name>.v<N>``."""
    assert is_json_program_type(alias) is expected


def test_json_program_type_matches_dicts_by_type():
    """The marker class matches a dict by its "type" and is the same class on each call."""
    marker = json_program_type("pulse.schedule.v1")
    assert marker is json_program_type("pulse.schedule.v1")
    assert isinstance(PULSE, marker)
    assert not isinstance({**PULSE, "type": "calibration.v1"}, marker)
    assert not isinstance("pulse.schedule.v1", marker)
    with pytest.raises(ValueError, match="not a JSON program type"):
        json_program_type("qasm3")


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
@pytest.mark.parametrize("program_type", ["calibration.v1", "acme.iq_trace.v1"])
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

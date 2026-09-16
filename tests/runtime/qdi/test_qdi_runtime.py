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

# pylint: disable=redefined-outer-name,protected-access

"""
Unit tests for the QDI provider, device, and job classes against an
in-memory QDI client.

"""

import pytest
import qiskit
from pyqasm.exceptions import PyQasmError

from qbraid.runtime import ResourceNotFoundError, load_job, load_provider
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.exceptions import ProgramValidationError
from qbraid.runtime.qdi import (
    QdiDevice,
    QdiDeviceDescriptor,
    QdiDeviceError,
    QdiError,
    QdiHttpClient,
    QdiJob,
    QdiJobError,
    QdiProvider,
    QdiStatus,
    QdiTaskStatus,
)

from .conftest import DEMO_MOCK, OQTOPUS_QULACS, QASM2_BELL, QASM3_BELL, FakeQdiClient, FakeQdiError

FAKE_CLIENT_PATH = "tests.runtime.qdi.conftest:FakeQdiClient"


# --------------------------------------------------------------------------- #
# Descriptor
# --------------------------------------------------------------------------- #


def test_descriptor_from_oqtopus_payload():
    """The OQTOPUS descriptor parses with ``display_name`` and no extras."""
    descriptor = QdiDeviceDescriptor.from_dict(OQTOPUS_QULACS)
    assert descriptor.device_id == "qulacs"
    assert descriptor.display_name == "Qulacs Simulator"
    assert descriptor.supported_task_types == ("openqasm3",)
    assert descriptor.num_qubits == 16
    assert descriptor.supports_estimation is False
    assert not descriptor.extra


def test_descriptor_keeps_undeclared_keys_as_extras():
    """Vendor keys the spec does not define survive in ``extra`` rather than being dropped."""
    descriptor = QdiDeviceDescriptor.from_dict(DEMO_MOCK)
    assert descriptor.extra == {"max_shots": 10000}


def test_descriptor_missing_required_field_fails_loudly():
    """A descriptor without a spec-required field raises at parse time, naming the key."""
    payload = {key: value for key, value in DEMO_MOCK.items() if key != "supported_extensions"}
    with pytest.raises(KeyError, match="supported_extensions"):
        QdiDeviceDescriptor.from_dict(payload)


# --------------------------------------------------------------------------- #
# Provider construction and client resolution
# --------------------------------------------------------------------------- #


def test_provider_requires_client_or_base_url(monkeypatch):
    """With neither a client nor a URL there is nothing to talk to."""
    monkeypatch.delenv("QDI_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="QDI_BASE_URL"):
        QdiProvider()


def test_provider_builds_http_client_from_env(monkeypatch):
    """``QDI_BASE_URL``/``QDI_API_TOKEN`` configure the HTTP client when no client is given."""
    monkeypatch.setenv("QDI_BASE_URL", "https://qdi.example.org/")
    monkeypatch.setenv("QDI_API_TOKEN", "env-token")
    provider = QdiProvider()
    assert isinstance(provider.client, QdiHttpClient)
    assert provider.client.base_url == "https://qdi.example.org"
    assert provider.client.headers["Authorization"] == "Bearer env-token"


def test_provider_rejects_url_with_explicit_client(fake_client):
    """``base_url`` only means something for the built-in HTTP client."""
    with pytest.raises(ValueError, match="only apply when no client is given"):
        QdiProvider(fake_client, base_url="https://qdi.example.org")


def test_provider_rejects_object_without_qdi_surface():
    """An object missing the six QDI methods is refused up front, not on first use."""
    with pytest.raises(TypeError, match="does not implement the QDI client surface"):
        QdiProvider(object())


def test_provider_resolves_client_from_import_path():
    """A ``"module:Class"`` string is imported and instantiated."""
    provider = QdiProvider(FAKE_CLIENT_PATH)
    assert isinstance(provider.client, FakeQdiClient)


def test_provider_resolves_client_from_dotted_path():
    """A ``"module.Class"`` string works too."""
    provider = QdiProvider("tests.runtime.qdi.conftest.FakeQdiClient")
    assert isinstance(provider.client, FakeQdiClient)


@pytest.mark.parametrize("spec", ["not_a_registered_vendor", "tests.runtime.qdi.conftest:Nope"])
def test_provider_unresolvable_client_spec(spec):
    """A name that is neither an entry point nor importable raises a ValueError naming it."""
    with pytest.raises(ValueError, match=spec.split(":")[0]):
        QdiProvider(spec)


def test_provider_rejects_resolved_class_without_qdi_surface():
    """A resolvable class that is not a QDI client is refused by type, before instantiation."""
    with pytest.raises(TypeError, match="does not implement the QDI client surface"):
        QdiProvider("tests.runtime.qdi.conftest:FakeQdiError")


def test_provider_explains_client_needing_constructor_args():
    """A real client class that needs arguments points the user at passing an instance."""
    with pytest.raises(ValueError, match="pass the instance to QdiProvider"):
        QdiProvider("tests.runtime.qdi.conftest:NeedsArgsQdiClient")


def test_load_provider_entrypoint(fake_client):
    """The provider is reachable through the ``qbraid.providers`` entry point."""
    provider = load_provider("qdi", client=fake_client)
    assert isinstance(provider, QdiProvider)


# --------------------------------------------------------------------------- #
# Handshake ordering
# --------------------------------------------------------------------------- #


def test_handshake_discover_then_authenticate(fake_client):
    """Against an open Discover, the device id from Discover is used for Authenticate."""
    provider = QdiProvider(fake_client, credentials={"token": "valid-token"})
    devices = provider.get_devices()
    assert [d.id for d in devices] == ["mock_qdi_qubit_v1"]
    assert fake_client.calls == [
        ("discover",),
        ("authenticate", "mock_qdi_qubit_v1", {"token": "valid-token"}),
    ]


def test_handshake_authenticate_then_discover(oqtopus_client):
    """Against OQTOPUS, whose Discover is closed, Authenticate runs first, then Discover again."""
    credentials = {"base_url": "https://demo-api.oqtopus.io", "api_token": "tok"}
    provider = QdiProvider(oqtopus_client, credentials=credentials)
    devices = provider.get_devices()
    assert [d.id for d in devices] == ["qulacs"]
    assert oqtopus_client.calls == [
        ("discover",),
        ("authenticate", "", credentials),
        ("discover",),
    ]


def test_handshake_runs_once(oqtopus_client):
    """Repeated discovery after the handshake does not re-authenticate."""
    credentials = {"base_url": "https://demo-api.oqtopus.io", "api_token": "tok"}
    provider = QdiProvider(oqtopus_client, credentials=credentials)
    provider.discover()
    provider.discover()
    assert [call[0] for call in oqtopus_client.calls].count("authenticate") == 1


def test_handshake_bad_credentials_surface_as_unauthorized(oqtopus_client):
    """A rejected Authenticate is a ``QdiError`` carrying ``ERROR_UNAUTHORIZED``."""
    provider = QdiProvider(oqtopus_client, credentials={"api_token": "wrong"})
    with pytest.raises(QdiError) as excinfo:
        provider.get_devices()
    assert excinfo.value.status == QdiStatus.ERROR_UNAUTHORIZED
    assert excinfo.value.operation == "authenticate"


def test_no_credentials_skips_authenticate(fake_client):
    """A pre-authenticated (or token-bearing) client is never asked to authenticate."""
    provider = QdiProvider(fake_client)
    provider.get_devices()
    assert all(call[0] != "authenticate" for call in fake_client.calls)


def test_closed_discover_without_credentials_propagates(oqtopus_client):
    """With no credentials to fall back on, a closed Discover is the caller's error to see."""
    with pytest.raises(QdiError) as excinfo:
        QdiProvider(oqtopus_client).get_devices()
    assert excinfo.value.status == QdiStatus.ERROR_UNAUTHORIZED


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #


def test_profile_from_demo_descriptor(fake_client):
    """Task types map onto qBraid program specs; unmapped ones stay in the profile."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")
    assert isinstance(device, QdiDevice)
    assert device.num_qubits == 32
    assert device.simulator is False
    assert [spec.alias for spec in device.profile.program_spec] == ["qasm3", "qasm2"]
    assert device.profile["supported_task_types"] == ["openqasm3", "openqasm2", "qir"]
    assert device.profile["supports_estimation"] is True
    assert device.profile["display_name"] == "Mock QDI QPU"
    assert device.profile.provider_name == "QDI"


def test_profile_from_oqtopus_descriptor(oqtopus_client):
    """OQTOPUS declares OpenQASM 3 only, so only the ``qasm3`` spec is offered."""
    provider = QdiProvider(
        oqtopus_client, credentials={"base_url": "https://demo-api.oqtopus.io", "api_token": "tok"}
    )
    device = provider.get_device("qulacs")
    assert [spec.alias for spec in device.profile.program_spec] == ["qasm3"]
    assert device.num_qubits == 16
    assert "qiskit" in device.supported_run_inputs()


def test_profile_honors_vendor_simulator_flag():
    """A descriptor carrying ``device_type: simulator`` (spec extension) marks the device."""
    descriptor = {**OQTOPUS_QULACS, "device_type": "simulator"}
    device = QdiProvider(FakeQdiClient([descriptor])).get_device("qulacs")
    assert device.simulator is True


def test_get_device_not_found(fake_client):
    """An unknown device id raises ``ResourceNotFoundError``."""
    with pytest.raises(ResourceNotFoundError, match="nope"):
        QdiProvider(fake_client).get_device("nope")


# --------------------------------------------------------------------------- #
# Device
# --------------------------------------------------------------------------- #


def test_device_status_from_is_ready(fake_client):
    """``is_ready`` maps to ONLINE/UNAVAILABLE, disappearance to OFFLINE."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")
    assert device.status() == DeviceStatus.ONLINE
    fake_client.descriptors[0]["is_ready"] = False
    assert device.status() == DeviceStatus.UNAVAILABLE
    fake_client.descriptors.clear()
    assert device.status() == DeviceStatus.OFFLINE
    assert device.descriptor() is None


def test_run_qiskit_circuit_end_to_end(fake_client):
    """A Qiskit circuit is transpiled to OpenQASM 3 and sent as an ``openqasm3`` task."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")
    circuit = qiskit.QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    job = device.run(circuit, shots=100)
    assert isinstance(job, QdiJob)
    send = next(call for call in fake_client.calls if call[0] == "send")
    _, device_id, payload, task_type, shots, extensions = send
    assert device_id == "mock_qdi_qubit_v1"
    assert task_type == "openqasm3"
    assert shots == 100
    assert extensions is None
    assert isinstance(payload, bytes)
    assert payload.decode("utf-8").startswith("OPENQASM 3")

    result = job.result()
    assert result.success is True
    assert result.data.get_counts() == {"00": 52, "11": 48}
    assert result.details["task_type"] == "openqasm3"
    assert result.details["shots"] == 100


def test_submit_batch_returns_one_job_per_program(fake_client):
    """A list of programs becomes a list of QDI tasks in order."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")
    jobs = device.run([QASM3_BELL, QASM2_BELL], shots=10)
    assert [job.id for job in jobs] == ["task-1", "task-2"]
    task_types = [call[3] for call in fake_client.calls if call[0] == "send"]
    assert task_types == ["openqasm3", "openqasm2"]


def test_submit_picks_declared_task_type_alias():
    """A device that declares ``qasm3`` rather than ``openqasm3`` gets that spelling back."""
    descriptor = {**DEMO_MOCK, "supported_task_types": ["qasm3"]}
    client = FakeQdiClient([descriptor])
    device = QdiProvider(client).get_device("mock_qdi_qubit_v1")
    device.run(QASM3_BELL)
    assert client.calls[-1][3] == "qasm3"


def test_submit_rejects_dialect_device_does_not_declare(oqtopus_client):
    """OpenQASM 2 to an OpenQASM-3-only device fails before any round trip."""
    provider = QdiProvider(
        oqtopus_client, credentials={"base_url": "https://demo-api.oqtopus.io", "api_token": "tok"}
    )
    device = provider.get_device("qulacs")
    with pytest.raises(QdiDeviceError, match="none of which carry 'qasm2'"):
        device.submit(QASM2_BELL)
    assert all(call[0] != "send" for call in oqtopus_client.calls)


def test_run_transpiles_qasm2_for_qasm3_only_device(oqtopus_client):
    """Through ``run`` the same OpenQASM 2 program is converted rather than rejected."""
    provider = QdiProvider(
        oqtopus_client, credentials={"base_url": "https://demo-api.oqtopus.io", "api_token": "tok"}
    )
    device = provider.get_device("qulacs")
    device.run(QASM2_BELL)
    assert oqtopus_client.calls[-1][3] == "openqasm3"


def test_submit_rejects_undeclared_extension(fake_client):
    """Spec §3.2: undeclared extension keys are an error, never silently dropped."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")
    with pytest.raises(QdiDeviceError, match=r"\['mitigation_info'\]"):
        device.submit(QASM3_BELL, extensions={"mitigation_info": {}})


def test_submit_forwards_declared_extensions(fake_client):
    """Declared extension keys are passed through to ``send`` untouched."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")
    device.submit(QASM3_BELL, extensions={"transpiler_info": {"level": 3}})
    assert fake_client.calls[-1][5] == {"transpiler_info": {"level": 3}}


def test_run_validates_program_before_send(fake_client):
    """A malformed program is caught by the pyqasm validator, not by the device."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")
    with pytest.raises((ProgramValidationError, PyQasmError)):
        device.run("OPENQASM 3.0;\nqubit[2] q;\nnotagate q[0];")
    assert all(call[0] != "send" for call in fake_client.calls)


def test_estimate_goes_through_runtime_pipeline(fake_client):
    """``estimate`` transpiles like ``run`` and calls ``estimate_resources``."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")
    circuit = qiskit.QuantumCircuit(1)
    circuit.h(0)
    circuit.measure_all()
    estimate = device.estimate(circuit, shots=50)
    assert estimate["shots"] == 50
    call = fake_client.calls[-1]
    assert call[0] == "estimate"
    assert call[3] == "openqasm3"
    assert call[2].decode("utf-8").startswith("OPENQASM 3")


def test_estimate_unsupported(oqtopus_client):
    """A device declaring ``supports_estimation: false`` is refused locally."""
    provider = QdiProvider(
        oqtopus_client, credentials={"base_url": "https://demo-api.oqtopus.io", "api_token": "tok"}
    )
    device = provider.get_device("qulacs")
    with pytest.raises(QdiDeviceError, match="does not support resource estimation"):
        device.estimate(QASM3_BELL)


def test_vendor_error_translated_with_status(fake_client):
    """A vendor exception carrying ``status`` becomes a ``QdiError`` with that status."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")

    def failing_send(*_args, **_kwargs):
        raise FakeQdiError(6, "cryostat warm")

    fake_client.send = failing_send
    with pytest.raises(QdiError) as excinfo:
        device.submit(QASM3_BELL)
    assert excinfo.value.status == QdiStatus.ERROR_HARDWARE_FAULT
    assert excinfo.value.operation == "send"
    assert "cryostat warm" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, FakeQdiError)


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (ConnectionError("refused"), QdiStatus.ERROR_CONNECTION_FAILED),
        (TimeoutError(), QdiStatus.ERROR_CONNECTION_FAILED),
        (RuntimeError("boom"), QdiStatus.ERROR_UNKNOWN),
        (FakeQdiError(12345, "not a qdi code"), QdiStatus.ERROR_UNKNOWN),
    ],
)
def test_statusless_errors_translated(fake_client, exc, expected):
    """Errors without a usable QDI status still surface as ``QdiError``, chained."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")

    def failing_discover():
        raise exc

    fake_client.discover = failing_discover
    with pytest.raises(QdiError) as excinfo:
        device.status()
    assert excinfo.value.status == expected
    assert excinfo.value.__cause__ is exc


# --------------------------------------------------------------------------- #
# Job
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("task_status", "job_status"),
    [
        (QdiTaskStatus.QUEUED, JobStatus.QUEUED),
        (QdiTaskStatus.EXECUTING, JobStatus.RUNNING),
        (QdiTaskStatus.COMPLETED, JobStatus.COMPLETED),
        (QdiTaskStatus.FAULTED, JobStatus.FAILED),
        (QdiTaskStatus.CANCELLED, JobStatus.CANCELLED),
    ],
)
def test_job_status_mapping(task_status, job_status):
    """Each of the five QDI states maps onto the matching qBraid status."""
    client = FakeQdiClient(statuses=[int(task_status)])
    device = QdiProvider(client).get_device("mock_qdi_qubit_v1")
    job = device.submit(QASM3_BELL)
    assert job.status() == job_status
    assert job.metadata()["advisory"] == {"queue_position": 0}


def test_job_unknown_status_value_raises():
    """An integer outside the five states is an error, not ``UNKNOWN``."""
    client = FakeQdiClient(statuses=[7])
    job = QdiProvider(client).get_device("mock_qdi_qubit_v1").submit(QASM3_BELL)
    with pytest.raises(QdiJobError, match="not one of"):
        job.status()


def test_job_result_waits_through_states(monkeypatch):
    """``result`` polls QUEUED -> EXECUTING -> COMPLETED before receiving."""
    monkeypatch.setattr("qbraid.runtime.job.sleep", lambda _seconds: None)
    client = FakeQdiClient(statuses=[0, 1, 2])
    job = QdiProvider(client).get_device("mock_qdi_qubit_v1").submit(QASM3_BELL)
    result = job.result()
    monitors = [call for call in client.calls if call[0] == "monitor"]
    assert len(monitors) >= 3
    assert all(call[0] != "receive" for call in client.calls[:-1])
    assert result.device_id == "mock_qdi_qubit_v1"
    assert result.job_id == job.id
    assert result.details["result_type"] == "counts"
    assert result.details["advisory"] == {"queue_position": 0}


def test_job_result_on_faulted_task():
    """A FAULTED task raises with the advisory metadata in the message."""
    client = FakeQdiClient(statuses=[3])
    job = QdiProvider(client).get_device("mock_qdi_qubit_v1").submit(QASM3_BELL)
    with pytest.raises(QdiJobError, match="FAILED"):
        job.result()
    assert all(call[0] != "receive" for call in client.calls)


def test_job_result_rejects_unknown_result_type():
    """A ``result_type`` other than counts is refused rather than misparsed."""
    client = FakeQdiClient(statuses=[2], result_type="samples")
    job = QdiProvider(client).get_device("mock_qdi_qubit_v1").submit(QASM3_BELL)
    with pytest.raises(QdiJobError, match="'samples'"):
        job.result()


def test_job_result_rejects_non_histogram_counts():
    """A counts payload that is not a dict is refused."""
    client = FakeQdiClient(statuses=[2], counts=[1, 0, 1])
    job = QdiProvider(client).get_device("mock_qdi_qubit_v1").submit(QASM3_BELL)
    with pytest.raises(QdiJobError, match="not a histogram"):
        job.result()


def test_job_cancel_unsupported(fake_client):
    """QDI v0.2 has no Cancel; the job says so instead of pretending."""
    job = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1").submit(QASM3_BELL)
    with pytest.raises(QdiJobError, match="no Cancel operation"):
        job.cancel()


def test_job_requires_client_and_device_id(fake_client):
    """A job needs both a client and a device id, directly or via ``device``."""
    with pytest.raises(ValueError, match="requires a QDI client"):
        QdiJob("task-1")
    with pytest.raises(ValueError, match="requires a device_id"):
        QdiJob("task-1", client=fake_client)


def test_load_job_rehydrates_from_task_and_device_id(fake_client):
    """``load_job`` reconstructs a job that can poll and fetch without a device object."""
    device = QdiProvider(fake_client).get_device("mock_qdi_qubit_v1")
    submitted = device.submit(QASM3_BELL)
    job = load_job(submitted.id, "qdi", client=fake_client, device_id=device.id)
    assert isinstance(job, QdiJob)
    assert job.device_id == "mock_qdi_qubit_v1"
    assert job.result().data.get_counts() == {"00": 52, "11": 48}
    with pytest.raises(ResourceNotFoundError):
        _ = job.device

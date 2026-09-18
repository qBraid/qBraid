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

# pylint: disable=missing-function-docstring,redefined-outer-name,too-many-statements
# pylint: disable=unsubscriptable-object,unused-argument

"""Unit tests for the IQM runtime integration."""

from __future__ import annotations

import importlib
import json
import sys
import uuid
from dataclasses import dataclass, field
from enum import Enum
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import Mock

import numpy as np
import pytest
from iqm.iqm_client import Circuit as RealIQMCircuit
from qiskit import QuantumCircuit

from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.iqm import IQMProgram
from qbraid.runtime import (
    BatchResult,
    GateModelResultData,
    ResourceNotFoundError,
    Result,
    TargetProfile,
)
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.iqm import (
    IQMDevice,
    IQMDeviceError,
    IQMJob,
    IQMJobError,
    IQMProvider,
    IQMSession,
)
from qbraid.runtime.iqm import provider as iqm_provider
from qbraid.transpiler.conversions.qiskit import qiskit_to_iqm
from qbraid.transpiler.exceptions import ProgramConversionError

importlib.import_module("qbraid.transpiler.conversions.qiskit.qiskit_to_iqm")
qiskit_to_iqm_module = sys.modules["qbraid.transpiler.conversions.qiskit.qiskit_to_iqm"]
from qbraid.runtime.iqm.job import _format_measurement_memory, _format_measurement_results


class FakeJobStatus(str, Enum):
    """Minimal IQM job status enum for tests."""

    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FakeMeasurementKey:
    """Minimal public IQM measurement-key helper."""

    def __init__(self, creg_idx: int, creg_len: int, clbit_idx: int):
        self.creg_idx = creg_idx
        self.creg_len = creg_len
        self.clbit_idx = clbit_idx

    def __str__(self) -> str:
        return f"register[{self.creg_idx}][{self.clbit_idx}]"

    @classmethod
    def from_string(cls, key: str):
        _, creg_len, creg_idx, clbit_idx = key.rsplit("_", 3)
        return cls(int(creg_idx), int(creg_len), int(clbit_idx))


@dataclass
class FakeGateInfo:
    """Minimal gate info model for tests."""

    loci: tuple[tuple[str, ...], ...] = ()


@dataclass
class FakeStaticArchitecture:
    """Minimal static architecture model for tests."""

    dut_label: str | None
    qubits: list[str]
    computational_resonators: list[str]
    connectivity: list[tuple[str, ...]]


@dataclass
class FakeDynamicArchitecture:
    """Minimal dynamic architecture model for tests."""

    calibration_set_id: uuid.UUID
    qubits: list[str]
    computational_resonators: list[str]
    gates: dict[str, FakeGateInfo]


@dataclass
class FakeCompilation:
    """Minimal compilation metadata."""

    calibration_set_id: uuid.UUID | None = None


@dataclass
class FakeJobData:
    """Minimal IQM job payload."""

    id: uuid.UUID
    status: FakeJobStatus
    messages: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    queue_position: int | None = None
    timeline: list[str] = field(default_factory=list)
    compilation: FakeCompilation | None = None


@dataclass
class FakeCircuitOperation:
    """Minimal IQM circuit operation."""

    name: str
    locus: tuple[str, ...]
    args: dict[str, object]
    implementation: str | None = None


@dataclass
class FakeCircuit:
    """Minimal IQM circuit."""

    name: str
    instructions: tuple[FakeCircuitOperation, ...]
    metadata: dict[str, object] | None = None


@dataclass
class FakeCompilationOptions:
    """Minimal IQM compilation options."""

    heralding_mode: object = None
    max_circuit_duration_over_t2: object = None


@dataclass
class FakeCircuitJob:
    """Minimal IQM circuit job wrapper."""

    job_id: uuid.UUID
    data: FakeJobData

    @property
    def status(self) -> FakeJobStatus:
        return self.data.status


FAKE_STATIC_ARCHITECTURES = {
    "garnet": FakeStaticArchitecture(
        dut_label="M138_W0_A22_Z99",
        qubits=["QB1", "QB2", "QB3"],
        computational_resonators=[],
        connectivity=[("QB1", "QB2"), ("QB2", "QB3")],
    ),
    "emerald": FakeStaticArchitecture(
        dut_label="M149_W1_A05_Z12",
        qubits=["QB1", "QB2"],
        computational_resonators=[],
        connectivity=[("QB1", "QB2")],
    ),
    "sirius": FakeStaticArchitecture(
        dut_label="M152_W2_A07_Z11",
        qubits=["QB1", "QB2"],
        computational_resonators=["CR1"],
        connectivity=[("QB1", "QB2")],
    ),
}
FAKE_DYNAMIC_ARCHITECTURES = {
    "garnet": FakeDynamicArchitecture(
        calibration_set_id=uuid.uuid4(),
        qubits=FAKE_STATIC_ARCHITECTURES["garnet"].qubits,
        computational_resonators=[],
        gates={
            "prx": FakeGateInfo(loci=(("QB1",), ("QB2",), ("QB3",))),
            "cz": FakeGateInfo(loci=(("QB1", "QB2"), ("QB2", "QB3"))),
            "measure": FakeGateInfo(),
            "barrier": FakeGateInfo(),
            "reset": FakeGateInfo(),
        },
    ),
    "emerald": FakeDynamicArchitecture(
        calibration_set_id=uuid.uuid4(),
        qubits=FAKE_STATIC_ARCHITECTURES["emerald"].qubits,
        computational_resonators=[],
        gates={
            "prx": FakeGateInfo(loci=(("QB1",), ("QB2",))),
            "cz": FakeGateInfo(loci=(("QB1", "QB2"),)),
            "measure": FakeGateInfo(),
            "barrier": FakeGateInfo(),
            "reset": FakeGateInfo(),
        },
    ),
    "sirius": FakeDynamicArchitecture(
        calibration_set_id=uuid.uuid4(),
        qubits=FAKE_STATIC_ARCHITECTURES["sirius"].qubits,
        computational_resonators=FAKE_STATIC_ARCHITECTURES["sirius"].computational_resonators,
        gates={
            "prx": FakeGateInfo(loci=(("QB1",), ("QB2",))),
            "cz": FakeGateInfo(loci=(("QB1", "CR1"), ("QB2", "CR1"))),
            "move": FakeGateInfo(loci=(("QB1", "CR1"), ("QB2", "CR1"))),
            "measure": FakeGateInfo(),
            "barrier": FakeGateInfo(),
            "reset": FakeGateInfo(),
        },
    ),
}
FAKE_IQM_ALIASES = tuple(FAKE_STATIC_ARCHITECTURES)


class FakeIQMClient:
    operational_status = "online"
    """Fake IQM client with class-level fixtures."""

    aliases = FAKE_IQM_ALIASES
    static_architectures = FAKE_STATIC_ARCHITECTURES
    dynamic_architectures = FAKE_DYNAMIC_ARCHITECTURES
    jobs: ClassVar[dict[uuid.UUID, FakeCircuitJob]] = {}
    measurements: ClassVar[dict[uuid.UUID, list[dict[str, list[list[int]]]]]] = {}
    dynamic_architecture_requests: ClassVar[list[uuid.UUID | None]] = []
    submitted_call: ClassVar[dict[str, object] | None] = None

    def __init__(
        self,
        iqm_server_url: str,
        *,
        quantum_computer: str | None = None,
        token: str | None = None,
        tokens_file: str | None = None,
        client_signature: str | None = None,
    ):
        self.iqm_server_url = iqm_server_url
        self.quantum_computer = quantum_computer
        self.token = token
        self.tokens_file = tokens_file
        self.client_signature = client_signature

    def get_static_quantum_architecture(self):
        alias = self.quantum_computer or type(self).aliases[0]
        return type(self).static_architectures[alias]

    def get_dynamic_quantum_architecture(self, calibration_set_id=None):
        type(self).dynamic_architecture_requests.append(calibration_set_id)
        alias = self.quantum_computer or type(self).aliases[0]
        return type(self).dynamic_architectures[alias]

    def submit_circuits(self, circuits, **kwargs):
        job_id = uuid.uuid4()
        job = FakeCircuitJob(
            job_id=job_id,
            data=FakeJobData(
                id=job_id,
                status=FakeJobStatus.WAITING,
                compilation=FakeCompilation(kwargs.get("calibration_set_id")),
            ),
        )
        type(self).jobs[job_id] = job
        type(self).submitted_call = {"circuits": circuits, **kwargs}
        return job

    def get_job(self, job_id):
        return type(self).jobs[job_id]

    def get_job_measurements(self, job_id):
        return type(self).measurements[job_id]

    def cancel_job(self, job_id):
        type(self).jobs[job_id].data.status = FakeJobStatus.CANCELLED

    def get_health(self):
        return {"operational_status": type(self).operational_status}


@pytest.fixture
def fake_symbols(monkeypatch):
    """Patch the IQM symbol loader with fake classes."""

    def fake_serialize_instructions(
        circuit,
        qubit_index_to_name,
        allowed_nonnative_gates=(),
        *,
        clbit_to_measure=None,
        overwrite_layout=None,
    ):
        del allowed_nonnative_gates, overwrite_layout
        clbit_to_measure = {} if clbit_to_measure is None else clbit_to_measure
        instructions = []

        for circuit_instruction in circuit.data:
            operation = circuit_instruction.operation
            qubit_names = tuple(
                qubit_index_to_name[circuit.find_bit(qubit).index]
                for qubit in circuit_instruction.qubits
            )

            if operation.name == "r":
                native_instruction = FakeCircuitOperation(
                    name="prx",
                    locus=qubit_names,
                    args={
                        "angle": float(operation.params[0]),
                        "phase": float(operation.params[1]),
                    },
                )
            elif operation.name == "cz":
                native_instruction = FakeCircuitOperation(name="cz", locus=qubit_names, args={})
            elif operation.name == "measure":
                clbit = circuit_instruction.clbits[0]
                bitloc = circuit.find_bit(clbit)
                creg = bitloc.registers[0][0]
                measurement_key = (
                    f"{creg.name}_{len(creg)}_{circuit.cregs.index(creg)}_"
                    f"{bitloc.registers[0][1]}"
                )
                native_instruction = FakeCircuitOperation(
                    name="measure",
                    locus=qubit_names,
                    args={"key": measurement_key},
                )
                clbit_to_measure[clbit] = native_instruction
            elif operation.name == "barrier":
                native_instruction = FakeCircuitOperation(
                    name="barrier", locus=qubit_names, args={}
                )
            elif operation.name == "reset":
                native_instruction = FakeCircuitOperation(name="reset", locus=qubit_names, args={})
            else:
                raise ValueError(
                    f"Unsupported instruction '{operation.name}' in fake IQM serializer."
                )

            instructions.append(native_instruction)

        return instructions

    def fake_transpile_insert_moves(
        circuit, architecture, *, existing_moves=None, qubit_mapping=None, restore_states=True
    ):
        del existing_moves, qubit_mapping, restore_states
        move_loci = tuple(getattr(architecture.gates.get("move"), "loci", ()))
        cz_loci = tuple(getattr(architecture.gates.get("cz"), "loci", ()))
        if not move_loci:
            return circuit

        instructions = []
        for instruction in circuit.instructions:
            if instruction.name != "cz" or instruction.locus in cz_loci:
                instructions.append(instruction)
                continue

            resolution = None
            qubit_a, qubit_b = instruction.locus
            for gate_qubit, resonator in cz_loci:
                if gate_qubit == qubit_a and (qubit_b, resonator) in move_loci:
                    resolution = (qubit_a, qubit_b, resonator)
                    break
                if gate_qubit == qubit_b and (qubit_a, resonator) in move_loci:
                    resolution = (qubit_b, qubit_a, resonator)
                    break

            if resolution is None:
                raise ValueError(f"No MOVE routing available for CZ locus {instruction.locus}.")

            gate_qubit, move_qubit, resonator = resolution
            instructions.extend(
                (
                    FakeCircuitOperation(name="move", locus=(move_qubit, resonator), args={}),
                    FakeCircuitOperation(name="cz", locus=(gate_qubit, resonator), args={}),
                    FakeCircuitOperation(name="move", locus=(move_qubit, resonator), args={}),
                )
            )

        return FakeCircuit(
            name=circuit.name, instructions=tuple(instructions), metadata=circuit.metadata
        )

    symbols = SimpleNamespace(
        IQMClient=FakeIQMClient,
        JobStatus=FakeJobStatus,
        CircuitCompilationOptions=FakeCompilationOptions,
        ExistingMoveHandlingOptions=SimpleNamespace(KEEP="keep"),
        transpile_insert_moves=fake_transpile_insert_moves,
        Circuit=RealIQMCircuit,
        CircuitOperation=FakeCircuitOperation,
    )
    monkeypatch.setattr("qbraid.runtime.iqm.device.iqm_client", symbols)
    monkeypatch.setattr("qbraid.runtime.iqm.provider.iqm_client", symbols)
    monkeypatch.setattr(qiskit_to_iqm_module, "iqm_client", symbols)
    monkeypatch.setattr(
        qiskit_to_iqm_module,
        "qiskit_to_iqm_",
        SimpleNamespace(serialize_instructions=fake_serialize_instructions),
    )
    monkeypatch.setattr(
        qiskit_to_iqm_module,
        "qiskit_",
        SimpleNamespace(transpile=lambda circuit, **kwargs: circuit),
    )
    monkeypatch.setattr(
        "qbraid.runtime.iqm.provider.list_quantum_computers",
        lambda *args, **kwargs: FakeIQMClient.aliases,
    )
    FakeIQMClient.jobs = {}
    FakeIQMClient.measurements = {}
    FakeIQMClient.dynamic_architecture_requests = []
    FakeIQMClient.submitted_call = None
    return symbols


@pytest.fixture
def profile():
    """Return an IQM target profile for tests."""
    qubits = FakeIQMClient.static_architectures["garnet"].qubits
    return TargetProfile(
        device_id="garnet",
        simulator=False,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=len(qubits),
        program_spec=ProgramSpec(RealIQMCircuit, alias="iqm"),
        provider_name="IQM",
        basis_gates=["r", "cz"],
        quantum_computer="garnet",
        dut_label=FakeIQMClient.static_architectures["garnet"].dut_label,
        qubits=tuple(FakeIQMClient.static_architectures["garnet"].qubits),
        qubit_connectivity=tuple(FakeIQMClient.static_architectures["garnet"].connectivity),
    )


def test_iqm_provider_get_device_and_devices(fake_symbols):
    """Test building IQM devices from an account-scoped provider."""
    provider = IQMProvider(url="https://demo.iqm.fi", token="secret")

    assert isinstance(provider.session, IQMSession)
    assert provider.session.url == "https://demo.iqm.fi"
    assert provider.session.quantum_computer is None
    assert provider.session.client_signature.startswith("QbraidSDK/")

    devices = provider.get_devices()
    assert len(devices) == 3
    assert {device.id for device in devices} == {"garnet", "emerald", "sirius"}
    assert all(isinstance(device, IQMDevice) for device in devices)

    garnet = next(device for device in devices if device.id == "garnet")
    assert garnet.profile.basis_gates == {"r", "cz"}
    assert garnet.profile["qubits"] == tuple(FakeIQMClient.static_architectures["garnet"].qubits)
    sirius = next(device for device in devices if device.id == "sirius")
    assert sirius.profile.basis_gates == {"r", "cz", "move"}

    device = provider.get_device("garnet")
    assert isinstance(device, IQMDevice)
    assert device.profile["native_operations"] == tuple(
        sorted(FakeIQMClient.dynamic_architectures["garnet"].gates.keys())
    )
    assert device.profile["dut_label"] == FakeIQMClient.static_architectures["garnet"].dut_label


def test_iqm_provider_scoped_quantum_computer(fake_symbols):
    """Test that a scoped provider returns only the selected quantum computer."""
    provider = IQMProvider(url="https://demo.iqm.fi", quantum_computer="garnet")

    devices = provider.get_devices()
    assert len(devices) == 1
    assert devices[0].id == "garnet"
    assert devices[0].profile["dut_label"] == FakeIQMClient.static_architectures["garnet"].dut_label


def test_iqm_provider_missing_device(fake_symbols):
    """Test missing IQM device lookup."""
    provider = IQMProvider(url="https://demo.iqm.fi")

    with pytest.raises(ResourceNotFoundError, match=r"Device 'fake-device' not found\."):
        provider.get_device("fake-device")


def test_list_quantum_computers_request(monkeypatch):
    """Test the account-level IQM device-listing request."""
    captured = {}

    class FakeClientConfigurationError(Exception):
        """Minimal configuration error type."""

    class FakeTokenManager:
        """Minimal token manager for auth header generation."""

        def __init__(self, token, tokens_file):
            self.token = token
            self.tokens_file = tokens_file

        def get_auth_header_callback(self):
            return lambda: f"Bearer {self.token}"

    class FakeListQuantumComputersResponse:
        """Minimal response model."""

        @classmethod
        def model_validate_json(cls, payload: str):
            data = json.loads(payload)
            return SimpleNamespace(
                quantum_computers=tuple(
                    SimpleNamespace(alias=entry["alias"]) for entry in data["quantum_computers"]
                )
            )

    class FakeResponse:
        """Minimal HTTP response."""

        ok = True
        text = json.dumps({"quantum_computers": [{"alias": "garnet"}, {"alias": "sirius"}]})

        def json(self):
            return json.loads(self.text)

    def fake_get(url, *, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        iqm_provider,
        "iqm_server_client",
        SimpleNamespace(
            REQUESTS_TIMEOUT=12.5,
            ListQuantumComputersResponse=FakeListQuantumComputersResponse,
            map_from_status_code_to_error=lambda status_code: RuntimeError,
        ),
    )
    monkeypatch.setattr(
        iqm_provider,
        "iqm_authentication",
        SimpleNamespace(
            ClientConfigurationError=FakeClientConfigurationError,
            TokenManager=FakeTokenManager,
        ),
    )
    monkeypatch.setattr(iqm_provider.requests, "get", fake_get)

    aliases = iqm_provider.list_quantum_computers(
        "https://resonance.meetiqm.com/",
        token="secret",
        client_signature="QbraidSDK/test",
    )

    assert aliases == ("garnet", "sirius")
    assert captured["url"] == "https://resonance.meetiqm.com/api/v1/quantum-computers"
    assert captured["timeout"] == 12.5
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["headers"]["User-Agent"].endswith(", QbraidSDK/test")


def test_list_quantum_computers_rejects_non_base_url(monkeypatch):
    """Test server URL normalization now requires a base server URL."""

    class FakeClientConfigurationError(Exception):
        """Minimal configuration error type."""

    monkeypatch.setattr(
        iqm_provider,
        "iqm_authentication",
        SimpleNamespace(ClientConfigurationError=FakeClientConfigurationError),
    )

    with pytest.raises(
        FakeClientConfigurationError,
        match=r"must be a server base URL without a quantum computer path",
    ):
        iqm_provider.list_quantum_computers("https://resonance.meetiqm.com/garnet")


def test_iqm_session_defaults_from_environment(monkeypatch):
    """Test default Resonance URL without copying token env vars into init args."""
    monkeypatch.delenv("IQM_SERVER_URL", raising=False)
    monkeypatch.delenv("IQM_QUANTUM_COMPUTER", raising=False)
    monkeypatch.setenv("IQM_TOKEN", "secret")

    session = IQMSession()

    assert session.url == "https://resonance.meetiqm.com"
    assert session._token is None
    assert session.quantum_computer is None


def test_iqm_device_status(profile):
    """Test IQM device status mapping."""
    session = Mock()
    device = IQMDevice(profile=profile, session=session)

    session.get_health.return_value = {"operational_status": "online"}
    assert device.status() == DeviceStatus.ONLINE

    session.get_health.return_value = {"operational_status": "maintenance"}
    assert device.status() == DeviceStatus.UNAVAILABLE

    session.get_health.return_value = {"operational_status": "offline"}
    assert device.status() == DeviceStatus.OFFLINE

    # A status IQM adds later must fail loudly rather than read as available.
    session.get_health.return_value = {"operational_status": "rebooting"}
    with pytest.raises(IQMDeviceError, match="Unrecognized operational status 'rebooting'"):
        device.status()


def test_iqm_job_status_and_cancel(profile):
    """Test IQM job status mapping and cancellation."""
    job_id = uuid.uuid4()
    session = Mock()
    session.get_job.return_value = FakeCircuitJob(
        job_id=job_id,
        data=FakeJobData(id=job_id, status=FakeJobStatus.WAITING),
    )
    job = IQMJob(job_id=str(job_id), session=session)

    assert job.status() == JobStatus.QUEUED

    job.cancel()
    session.cancel_job.assert_called_once_with(job.id)


@pytest.mark.parametrize(
    ("iqm_status", "qbraid_status"),
    [
        ("waiting", JobStatus.QUEUED),
        ("processing", JobStatus.RUNNING),
        ("completed", JobStatus.COMPLETED),
        ("failed", JobStatus.FAILED),
        ("cancelled", JobStatus.CANCELLED),
    ],
)
def test_iqm_job_maps_status_strings(iqm_status, qbraid_status):
    """Test IQM status strings map directly to qBraid statuses."""
    assert IQMJob._map_status(iqm_status) == qbraid_status


def test_iqm_job_rejects_unmapped_status():
    """A status IQM adds later fails loudly instead of degrading to UNKNOWN."""
    with pytest.raises(IQMJobError, match="Unrecognized IQM job status 'future-status'"):
        IQMJob._map_status("future-status")


def test_iqm_job_terminal_status_is_cached():
    """Test terminal job status does not trigger redundant server requests."""
    job_id = uuid.uuid4()
    session = Mock()
    session.get_job.return_value = FakeCircuitJob(
        job_id=job_id,
        data=FakeJobData(id=job_id, status=FakeJobStatus.COMPLETED),
    )
    job = IQMJob(job_id=str(job_id), session=session)

    assert job.status() == JobStatus.COMPLETED
    assert job.status() == JobStatus.COMPLETED
    session.get_job.assert_called_once_with(str(job_id))


def test_iqm_measurement_formatting(fake_symbols):
    """Test IQM measurement keys become memory, shot arrays, and counts."""
    memory, measurements, counts = _format_measurement_results(
        {
            "c_2_0_0": [[1], [0]],
            "c_2_0_1": [[0], [1]],
        }
    )

    assert memory == ["01", "10"]
    assert np.array_equal(measurements, np.array([[0, 1], [1, 0]]))
    assert counts == {"01": 1, "10": 1}


def test_iqm_job_result(fake_symbols, profile):
    """Test IQM result conversion into qBraid result data."""
    job_id = uuid.uuid4()
    session = Mock()
    device = IQMDevice(profile=profile, session=session)
    session.get_job.return_value = FakeCircuitJob(
        job_id=job_id,
        data=FakeJobData(
            id=job_id,
            status=FakeJobStatus.COMPLETED,
            messages=["queued"],
            compilation=FakeCompilation(
                FakeIQMClient.dynamic_architectures["garnet"].calibration_set_id
            ),
        ),
    )
    session.get_job_measurements.return_value = [
        {
            "c_2_0_0": [[1], [1], [0]],
            "c_2_0_1": [[0], [0], [1]],
        }
    ]

    job = IQMJob(
        job_id=str(job_id),
        session=session,
        device=device,
        circuit_count=1,
    )
    result = job.result()

    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert result.success is True
    assert result.data.get_counts() == {"01": 2, "10": 1}
    assert np.array_equal(result.data.measurements, np.array([[0, 1], [0, 1], [1, 0]]))
    assert result.details["status"] == JobStatus.COMPLETED
    assert result.details["messages"] == ["queued"]


def test_iqm_job_result_prefers_qbraid_device_id(fake_symbols, profile):
    """Test qBraid's device ID takes precedence over IQM's physical DUT label."""
    job_id = uuid.uuid4()
    session = Mock()
    session.quantum_computer = FakeIQMClient.static_architectures["garnet"].dut_label
    session.url = "https://demo.iqm.fi"
    device = IQMDevice(profile=profile, session=session)
    fetched_job = FakeCircuitJob(
        job_id=job_id,
        data=FakeJobData(
            id=job_id,
            status=FakeJobStatus.COMPLETED,
            messages=["queued"],
        ),
    )
    session.get_job.return_value = fetched_job
    session.get_job_measurements.return_value = [
        {
            "c_1_0_0": [[1], [0]],
        }
    ]

    job = IQMJob(job_id=str(job_id), session=session, device=device)
    metadata = job.metadata()
    result = job.result()

    assert metadata["device_id"] == "garnet"
    assert result.device_id == "garnet"


def test_iqm_batch_job_result(fake_symbols, profile):
    """Test one multi-circuit IQM job returns qBraid's BatchResult."""
    job_id = uuid.uuid4()
    session = Mock()
    device = IQMDevice(profile=profile, session=session)
    session.get_job.return_value = FakeCircuitJob(
        job_id=job_id,
        data=FakeJobData(id=job_id, status=FakeJobStatus.COMPLETED),
    )
    session.get_job_measurements.return_value = [
        {"c_1_0_0": [[0], [1]]},
        {"c_1_0_0": [[1], [1]]},
    ]

    result = IQMJob(
        job_id=str(job_id),
        session=session,
        device=device,
        circuit_count=2,
    ).result()

    assert isinstance(result, BatchResult)
    assert result.num_circuits == 2
    assert [circuit.data.get_counts() for circuit in result.results] == [
        {"0": 1, "1": 1},
        {"1": 2},
    ]
    assert result.data.get_counts() == [{"0": 1, "1": 1}, {"1": 2}]


def test_iqm_job_result_failure():
    """Test IQM failure propagation."""
    job_id = uuid.uuid4()
    session = Mock()
    session.get_job.return_value = FakeCircuitJob(
        job_id=job_id,
        data=FakeJobData(
            id=job_id,
            status=FakeJobStatus.FAILED,
            errors=["Compilation failed"],
        ),
    )

    job = IQMJob(job_id=str(job_id), session=session)
    with pytest.raises(IQMJobError, match="Compilation failed"):
        job.result()


def test_qiskit_to_iqm_is_device_independent():
    """The conversion emits logical names and needs no device context."""
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    converted = qiskit_to_iqm(circuit)

    loci = {qubit for op in converted.instructions for qubit in op.locus}
    assert loci <= {"q_0", "q_1"}
    assert {op.name for op in converted.instructions} <= {"prx", "cz", "measure"}


def test_iqm_program_wraps_native_circuit():
    """IQMProgram reports the named qubits and measured bits of an IQM circuit."""
    circuit = QuantumCircuit(2, 2)
    circuit.x(0)
    circuit.measure([0, 1], [0, 1])
    program = IQMProgram(qiskit_to_iqm(circuit))

    assert program.qubits == ["q_0", "q_1"]
    assert program.num_qubits == 2
    assert program.num_clbits == 2


def test_iqm_program_rejects_other_types():
    """A non-IQM object is refused rather than silently wrapped."""
    with pytest.raises(ProgramTypeError):
        IQMProgram(QuantumCircuit(1))


def test_qubit_mapping_binds_logical_names_to_physical_qubits(profile):
    """The device, not the conversion, decides which physical qubits are used."""
    device = IQMDevice(profile=profile, session=Mock())
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    mapping = device.qubit_mapping_for(qiskit_to_iqm(circuit))

    assert set(mapping) == {"q_0", "q_1"}
    assert set(mapping.values()) <= set(device.qubits)


def test_qubit_mapping_is_none_for_physical_names(profile):
    """A circuit already using physical names needs no mapping."""
    device = IQMDevice(profile=profile, session=Mock())
    physical = device.qubits[:2]
    circuit = RealIQMCircuit(
        name="physical",
        instructions=(FakeCircuitOperation(name="cz", locus=tuple(physical), args={}),),
        metadata=None,
    )
    assert device.qubit_mapping_for(circuit) is None


def test_qubit_mapping_rejects_unplaceable_circuit(profile):
    """A circuit whose interactions cannot embed in the topology fails loudly."""
    device = IQMDevice(profile=profile, session=Mock())
    qubit_count = len(device.qubits) + 1
    circuit = QuantumCircuit(qubit_count)
    for index in range(qubit_count):
        for other in range(index + 1, qubit_count):
            circuit.cz(index, other)

    with pytest.raises(ValueError, match="No placement of"):
        device.qubit_mapping_for(qiskit_to_iqm(circuit))


def test_iqm_device_submit_places_circuits_on_physical_qubits(profile):
    """submit() resolves placement into each circuit's loci.

    IQM applies one ``qubit_mapping`` per batch, so circuits needing different
    placements could not share a job. Resolving placement per circuit keeps
    heterogeneous batches submittable.
    """
    session = Mock()
    session.submit_circuits.return_value = SimpleNamespace(job_id=uuid.uuid4())
    device = IQMDevice(profile=profile, session=session)

    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    device.submit(qiskit_to_iqm(circuit), shots=17)

    args, kwargs = session.submit_circuits.call_args
    assert kwargs["shots"] == 17
    assert kwargs["qubit_mapping"] is None

    submitted = args[0]
    loci = {qubit for circuit in submitted for op in circuit.instructions for qubit in op.locus}
    assert loci <= set(device.qubits)


def test_iqm_device_submit_respects_caller_supplied_mapping(profile):
    """An explicit qubit_mapping is forwarded untouched, and placement is skipped."""
    session = Mock()
    session.submit_circuits.return_value = SimpleNamespace(job_id=uuid.uuid4())
    device = IQMDevice(profile=profile, session=session)

    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    mapping = {"q_0": device.qubits[-1], "q_1": device.qubits[-2]}
    device.submit(qiskit_to_iqm(circuit), shots=5, qubit_mapping=mapping)

    _, kwargs = session.submit_circuits.call_args
    assert kwargs["qubit_mapping"] == mapping


def test_iqm_measurement_formatting_rejects_inconsistent_shots(fake_symbols):
    """Measurement keys disagreeing on shot count is a hard error."""
    results = {
        "c_2_0_0": [[0], [1]],
        "c_2_0_1": [[0]],
    }
    with pytest.raises(ValueError, match="Inconsistent number of shots"):
        _format_measurement_memory(results)


def test_cirq_to_iqm_handles_single_qubit_circuits():
    """IQM rejects an empty connectivity, so metadata is built for at least two qubits."""
    cirq = pytest.importorskip("cirq")
    from qbraid.transpiler.conversions.cirq import cirq_to_iqm

    qubit = cirq.LineQubit(0)
    converted = cirq_to_iqm(cirq.Circuit([cirq.X(qubit), cirq.measure(qubit, key="m")]))

    assert [op.name for op in converted.instructions] == ["prx", "measure"]


@pytest.mark.parametrize("source", ["qiskit", "cirq"])
def test_unresolved_parameters_are_named_not_leaked(source):
    """Symbolic gate parameters raise a qBraid error naming them, not a vendor TypeError."""
    sympy = pytest.importorskip("sympy")

    if source == "qiskit":
        from qiskit.circuit import Parameter

        from qbraid.transpiler.conversions.qiskit import qiskit_to_iqm as convert

        circuit = QuantumCircuit(1, 1)
        circuit.rx(Parameter("theta"), 0)
        circuit.measure(0, 0)
    else:
        cirq = pytest.importorskip("cirq")

        from qbraid.transpiler.conversions.cirq import cirq_to_iqm as convert

        qubit = cirq.LineQubit(0)
        circuit = cirq.Circuit([cirq.rx(sympy.Symbol("theta")).on(qubit)])

    with pytest.raises(ProgramConversionError, match="unresolved parameters: theta"):
        convert(circuit)


def test_transform_rejects_circuits_wider_than_the_device(profile):
    """An oversized circuit is named clearly, not left to qiskit's TranspilerError."""
    device = IQMDevice(profile=profile, session=Mock())
    width = device.num_qubits + 3
    circuit = QuantumCircuit(width, width)
    circuit.h(range(width))
    circuit.measure(range(width), range(width))

    with pytest.raises(ValueError, match="exceeds the device's capacity"):
        device.transform(qiskit_to_iqm(circuit))


def test_placement_leaves_computational_resonators_alone():
    """MOVE addresses a resonator by name; remapping it would invalidate the instruction."""
    qubits = ("QB1", "QB2", "QB3")
    resonators = ("COMPR1",)
    device_profile = TargetProfile(
        device_id="star",
        simulator=False,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=len(qubits),
        program_spec=ProgramSpec(RealIQMCircuit, alias="iqm"),
        provider_name="IQM",
        qubits=qubits,
        computational_resonators=resonators,
        qubit_connectivity=(("QB1", "QB2"), ("QB2", "QB3")),
    )
    device = IQMDevice(profile=device_profile, session=Mock())
    circuit = RealIQMCircuit(
        name="star",
        instructions=(
            FakeCircuitOperation(name="move", locus=("QB2", "COMPR1"), args={}),
            FakeCircuitOperation(name="cz", locus=("QB1", "QB2"), args={}),
        ),
        metadata=None,
    )

    assert device.qubit_mapping_for(circuit) is None
    assert "COMPR1" in device.components

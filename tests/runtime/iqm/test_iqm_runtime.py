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

# pylint: disable=redefined-outer-name

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import Mock
import uuid

import numpy as np
import pytest
from qiskit import QuantumCircuit

from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime import GateModelResultData, ResourceNotFoundError, Result, TargetProfile
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.iqm import IQMDevice, IQMJob, IQMJobError, IQMProvider, IQMSession


class FakeJobStatus(str, Enum):
    """Minimal IQM job status enum for tests."""

    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
    _iqm_client: object | None = None

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
    """Fake IQM client with class-level fixtures."""

    aliases = FAKE_IQM_ALIASES
    static_architectures = FAKE_STATIC_ARCHITECTURES
    dynamic_architectures = FAKE_DYNAMIC_ARCHITECTURES
    jobs: ClassVar[dict[uuid.UUID, FakeCircuitJob]] = {}
    measurements: ClassVar[dict[uuid.UUID, list[dict[str, list[list[int]]]]]] = {}
    dynamic_architecture_requests: ClassVar[list[uuid.UUID | None]] = []
    submitted_call: ClassVar[dict[str, object] | None] = None
    init_calls: ClassVar[int] = 0

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
        type(self).init_calls += 1

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
                native_instruction = FakeCircuitOperation(
                    name="measure",
                    locus=qubit_names,
                    args={
                        "key": f"{creg.name}_{len(creg)}_{circuit.cregs.index(creg)}_{bitloc.registers[0][1]}"
                    },
                )
                clbit_to_measure[clbit] = native_instruction
            elif operation.name == "barrier":
                native_instruction = FakeCircuitOperation(name="barrier", locus=qubit_names, args={})
            elif operation.name == "reset":
                native_instruction = FakeCircuitOperation(name="reset", locus=qubit_names, args={})
            else:
                raise ValueError(f"Unsupported instruction '{operation.name}' in fake IQM serializer.")

            instructions.append(native_instruction)

        return instructions

    def fake_format_measurement_results(measurement_results, requested_shots, expect_exact_shots):
        del requested_shots, expect_exact_shots
        formatted_results = {}
        shots = 0

        for key, values in measurement_results.items():
            _, creg_len, creg_idx, clbit_idx = key.rsplit("_", 3)
            result_array = np.asarray(values, dtype=int)
            if result_array.ndim == 1:
                result_array = result_array.reshape(-1, 1)
            shots = result_array.shape[0]
            classical_register = formatted_results.setdefault(
                int(creg_idx),
                np.zeros((shots, int(creg_len)), dtype=int),
            )
            classical_register[:, int(clbit_idx)] = result_array[:, 0]

        return [
            " ".join("".join(map(str, register[shot, :])) for _, register in sorted(formatted_results.items()))[::-1]
            for shot in range(shots)
        ]

    def fake_transpile_insert_moves(circuit, architecture, *, existing_moves=None, qubit_mapping=None, restore_states=True):
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

        return FakeCircuit(name=circuit.name, instructions=tuple(instructions), metadata=circuit.metadata)

    symbols = SimpleNamespace(
        IQMClient=FakeIQMClient,
        JobStatus=FakeJobStatus,
        CircuitCompilationOptions=FakeCompilationOptions,
        ExistingMoveHandlingOptions=SimpleNamespace(KEEP="keep"),
        transpile_insert_moves=fake_transpile_insert_moves,
        Circuit=FakeCircuit,
        CircuitOperation=FakeCircuitOperation,
    )
    monkeypatch.setattr("qbraid.runtime.iqm._compat.load_iqm_symbols", lambda: symbols)
    monkeypatch.setattr(
        "qbraid.runtime.iqm._compat.load_iqm_qiskit_symbols",
        lambda: SimpleNamespace(
            serialize_instructions=fake_serialize_instructions,
            format_measurement_results=fake_format_measurement_results,
        ),
    )
    monkeypatch.setattr(
        "qbraid.runtime.iqm._compat.list_quantum_computers",
        lambda *args, **kwargs: FakeIQMClient.aliases,
    )
    FakeIQMClient.jobs = {}
    FakeIQMClient.measurements = {}
    FakeIQMClient.dynamic_architecture_requests = []
    FakeIQMClient.submitted_call = None
    FakeIQMClient.init_calls = 0
    return symbols


@pytest.fixture
def profile():
    """Return an IQM target profile for tests."""
    return TargetProfile(
        device_id="garnet",
        simulator=False,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=len(FakeIQMClient.static_architectures["garnet"].qubits),
        program_spec=ProgramSpec(QuantumCircuit, alias="qiskit"),
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
    assert FakeIQMClient.init_calls == 0

    devices = provider.get_devices()
    assert FakeIQMClient.init_calls == 3
    assert len(devices) == 3
    assert {device.id for device in devices} == {"garnet", "emerald", "sirius"}
    assert all(isinstance(device, IQMDevice) for device in devices)

    garnet = next(device for device in devices if device.id == "garnet")
    assert garnet.profile.basis_gates == {"r", "cz"}
    assert garnet.profile["qubits"] == tuple(FakeIQMClient.static_architectures["garnet"].qubits)

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


def test_load_iqm_qiskit_symbols_without_private_iqm_job(monkeypatch):
    """Test qiskit helper loading without reaching into IQMJob private methods."""
    from qbraid.runtime.iqm import _compat

    class FakeMeasurementKey:
        """Minimal public measurement key helper."""

        def __init__(self, creg_idx: int, creg_len: int, clbit_idx: int):
            self.creg_idx = creg_idx
            self.creg_len = creg_len
            self.clbit_idx = clbit_idx

        @classmethod
        def from_string(cls, key: str):
            _, creg_len, creg_idx, clbit_idx = key.rsplit("_", 3)
            return cls(int(creg_idx), int(creg_len), int(clbit_idx))

    _compat.load_iqm_qiskit_symbols.cache_clear()

    def fake_import_module(name: str):
        if name == "iqm.qiskit_iqm.qiskit_to_iqm":
            return SimpleNamespace(
                serialize_instructions=Mock(name="serialize_instructions"),
                MeasurementKey=FakeMeasurementKey,
            )
        raise AssertionError(f"Unexpected import: {name}")

    monkeypatch.setattr(_compat, "import_module", fake_import_module)

    try:
        symbols = _compat.load_iqm_qiskit_symbols()
        results = symbols.format_measurement_results(
            {
                "m_2_0_0": [[1], [0]],
                "m_2_0_1": [[0], [1]],
            },
            0,
            False,
        )
        assert results == ["01", "10"]
    finally:
        _compat.load_iqm_qiskit_symbols.cache_clear()


def test_list_quantum_computers_without_private_server_client_helpers(monkeypatch):
    """Test account-level device listing without `_IQMServerClient` private helpers."""
    from qbraid.runtime.iqm import _compat

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

    def fake_import_module(name: str):
        if name == "iqm.iqm_server_client.iqm_server_client":
            return SimpleNamespace(
                REQUESTS_TIMEOUT=12.5,
                ListQuantumComputersResponse=FakeListQuantumComputersResponse,
                map_from_status_code_to_error=lambda status_code: RuntimeError,
            )
        if name == "iqm.station_control.client.authentication":
            return SimpleNamespace(
                ClientConfigurationError=FakeClientConfigurationError,
                TokenManager=FakeTokenManager,
            )
        if name == "requests":
            return SimpleNamespace(get=fake_get)
        raise AssertionError(f"Unexpected import: {name}")

    monkeypatch.setattr(_compat, "import_module", fake_import_module)

    aliases = _compat.list_quantum_computers(
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
    from qbraid.runtime.iqm import _compat

    class FakeClientConfigurationError(Exception):
        """Minimal configuration error type."""

    def fake_import_module(name: str):
        if name == "iqm.iqm_server_client.iqm_server_client":
            return SimpleNamespace(
                REQUESTS_TIMEOUT=12.5,
                ListQuantumComputersResponse=Mock(),
                map_from_status_code_to_error=lambda status_code: RuntimeError,
            )
        if name == "iqm.station_control.client.authentication":
            return SimpleNamespace(
                ClientConfigurationError=FakeClientConfigurationError,
                TokenManager=Mock(),
            )
        if name == "requests":
            return SimpleNamespace(get=Mock())
        raise AssertionError(f"Unexpected import: {name}")

    monkeypatch.setattr(_compat, "import_module", fake_import_module)

    with pytest.raises(
        FakeClientConfigurationError,
        match=r"must be a server base URL without a quantum computer path",
    ):
        _compat.list_quantum_computers("https://resonance.meetiqm.com/garnet")


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
    session.get_static_quantum_architecture.return_value = FakeIQMClient.static_architectures["garnet"]
    device = IQMDevice(profile=profile, session=session)
    assert device.status() == DeviceStatus.ONLINE

    session.get_static_quantum_architecture.side_effect = RuntimeError("offline")
    assert device.status() == DeviceStatus.UNAVAILABLE


def test_iqm_device_transform_and_prepare(fake_symbols, profile):
    """Test qiskit lowering to IQM instructions."""
    session = Mock()
    device = IQMDevice(profile=profile, session=session)

    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    transformed = device.transform(circuit)
    assert {instruction.operation.name for instruction in transformed.data} <= {"r", "cz", "measure"}

    prepared = device.prepare(transformed)
    assert isinstance(prepared, FakeCircuit)
    assert any(instruction.name == "prx" for instruction in prepared.instructions)
    assert any(instruction.name == "cz" for instruction in prepared.instructions)
    measure_keys = [instruction.args["key"] for instruction in prepared.instructions if instruction.name == "measure"]
    assert measure_keys == ["c_2_0_0", "c_2_0_1"]
    serialized_qubits = {
        qubit for instruction in prepared.instructions for qubit in instruction.locus
    }
    assert serialized_qubits <= set(FakeIQMClient.static_architectures["garnet"].qubits)


def test_iqm_device_submit(fake_symbols, profile):
    """Test submitting IQM circuits through the session wrapper."""
    provider = IQMProvider(url="https://demo.iqm.fi")
    device = provider.get_device("garnet")

    iqm_circuit = FakeCircuit(
        name="bell",
        instructions=(FakeCircuitOperation(name="measure", locus=("QB1",), args={"key": "c_1_0_0"}),),
        metadata={"num_clbits": 1},
    )

    job = device.submit(
        iqm_circuit,
        shots=32,
        max_circuit_duration_over_t2=0.5,
    )

    assert isinstance(job, IQMJob)
    assert job.device is device
    assert FakeIQMClient.submitted_call is not None
    assert FakeIQMClient.submitted_call["circuits"] == [iqm_circuit]
    assert FakeIQMClient.submitted_call["calibration_set_id"] == device.profile["calibration_set_id"]
    assert FakeIQMClient.submitted_call["shots"] == 32
    assert FakeIQMClient.submitted_call["options"] == FakeCompilationOptions(
        max_circuit_duration_over_t2=0.5
    )


def test_iqm_device_prepare_routes_fictional_cz(fake_symbols):
    """Test MOVE insertion for simplified qubit-qubit CZ loci on star architectures."""
    provider = IQMProvider(url="https://demo.iqm.fi")
    device = provider.get_device("sirius")

    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    transformed = device.transform(circuit)
    prepared = device.prepare(transformed)

    assert isinstance(prepared, FakeCircuit)
    assert sum(instruction.name == "move" for instruction in prepared.instructions) == 2
    assert any(instruction.name == "cz" and instruction.locus == ("QB1", "CR1") for instruction in prepared.instructions)
    assert all(
        not (instruction.name == "cz" and instruction.locus == ("QB1", "QB2"))
        for instruction in prepared.instructions
    )


def test_iqm_device_run_uses_one_calibration_set_for_prepare_and_submit(fake_symbols):
    """Test a per-run calibration set override is shared between MOVE insertion and submission."""
    provider = IQMProvider(url="https://demo.iqm.fi")
    device = provider.get_device("sirius")
    override_calibration_set_id = uuid.uuid4()
    baseline_requests = len(FakeIQMClient.dynamic_architecture_requests)

    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    job = device.run(circuit, shots=24, calibration_set_id=override_calibration_set_id)

    assert isinstance(job, IQMJob)
    assert FakeIQMClient.dynamic_architecture_requests[baseline_requests:] == [override_calibration_set_id]
    assert FakeIQMClient.submitted_call is not None
    assert FakeIQMClient.submitted_call["calibration_set_id"] == override_calibration_set_id


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


def test_iqm_job_result(profile):
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
            compilation=FakeCompilation(FakeIQMClient.dynamic_architectures["garnet"].calibration_set_id),
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


def test_iqm_job_loaded_result_prefers_job_specific_backend(profile):
    """Test loaded jobs use the backend encoded in the fetched IQM job, not the ambient session."""
    job_id = uuid.uuid4()
    session = Mock()
    session.quantum_computer = "emerald"
    session.url = "https://demo.iqm.fi"
    session.get_static_quantum_architecture = Mock()

    bound_client = SimpleNamespace(
        _iqm_server_client=SimpleNamespace(quantum_computer="garnet"),
        get_static_quantum_architecture=Mock(
            return_value=FakeIQMClient.static_architectures["garnet"]
        ),
    )
    fetched_job = FakeCircuitJob(
        job_id=job_id,
        data=FakeJobData(
            id=job_id,
            status=FakeJobStatus.COMPLETED,
            messages=["queued"],
        ),
        _iqm_client=bound_client,
    )
    session.get_job.return_value = fetched_job
    session.get_job_measurements.return_value = [
        {
            "c_1_0_0": [[1], [0]],
        }
    ]

    job = IQMJob(job_id=str(job_id), session=session)
    metadata = job.metadata()
    result = job.result()

    assert metadata["device_id"] == "garnet"
    assert result.device_id == "garnet"
    session.get_static_quantum_architecture.assert_not_called()


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

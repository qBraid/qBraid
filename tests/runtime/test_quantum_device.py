# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name,unused-argument

"""
Unit tests for QbraidDevice, QbraidJob, and QbraidGateModelResultBuilder
classes using the qbraid_qir_simulator

"""
import logging
import random
import time
import warnings
from typing import Any, Optional
from unittest.mock import MagicMock, Mock, patch

import cirq
import numpy as np
import pytest
from pandas import DataFrame
from pyqir import BasicQisBuilder, Module, SimpleModule
from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError

from qbraid._caching import cache_disabled
from qbraid.programs import ProgramSpec, register_program_type, unregister_program_type
from qbraid.runtime import DeviceStatus, ProgramValidationError, Result, TargetProfile
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import ExperimentType, JobStatus, NoiseModel
from qbraid.runtime.exceptions import QbraidRuntimeError, ResourceNotFoundError
from qbraid.runtime.native import QbraidDevice, QbraidJob, QbraidProvider
from qbraid.runtime.native.result_data import (
    QbraidQirSimulatorResultData,
    QuEraQasmSimulatorResultData,
)
from qbraid.runtime.native.schemas import RuntimeJobModel
from qbraid.transpiler import CircuitConversionError, Conversion, ConversionGraph, ConversionScheme

DEVICE_DATA_QIR = {
    "numberQubits": 64,
    "pendingJobs": 0,
    "qbraid_id": "qbraid_qir_simulator",
    "name": "QIR sparse simulator",
    "provider": "qBraid",
    "paradigm": "gate-based",
    "type": "SIMULATOR",
    "vendor": "qBraid",
    "runPackage": "pyqir",
    "status": "ONLINE",
    "isAvailable": True,
    "processorType": "State vector",
}

DEVICE_DATA_QUERA = {
    "numberQubits": 42,
    "pendingJobs": 0,
    "qbraid_id": "quera_qasm_simulator",
    "name": "Noisey QASM simulator",
    "provider": "QuEra",
    "paradigm": "gate-based",
    "type": "SIMULATOR",
    "vendor": "qBraid",
    "runPackage": "qasm2",
    "status": "ONLINE",
    "isAvailable": True,
    "processorType": "N.D.",
}

REDUNDANT_JOB_DATA = {
    "timeStamps": {
        "createdAt": "2024-05-23T01:39:11.288Z",
        "endedAt": "2024-05-23T01:39:11.304Z",
        "executionDuration": 16,
    },
    "measurementCounts": {"11111": 4, "00000": 6},
    "status": "COMPLETED",
}

JOB_DATA_QIR = {
    "qbraidJobId": "qbraid_qir_simulator-jovyan-qjob-1234567890",
    "queuePosition": None,
    "queueDepth": None,
    "shots": 10,
    "circuitNumQubits": 5,
    "qbraidDeviceId": "qbraid_qir_simulator",
    "vendor": "qbraid",
    "provider": "qbraid",
    "tags": {},
    **REDUNDANT_JOB_DATA,
}

JOB_DATA_QUERA = {
    "qbraidJobId": "quera_qasm_simulator-jovyan-qjob-1234567890",
    "queuePosition": None,
    "queueDepth": None,
    "shots": 10,
    "circuitNumQubits": 5,
    "qbraidDeviceId": "quera_qasm_simulator",
    "vendor": "qbraid",
    "provider": "quera",
    "tags": {},
    **REDUNDANT_JOB_DATA,
}

RESULTS_DATA_QIR = {
    "measurements": [
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
    ],
    "runnerVersion": "0.7.4",
    "runnerSeed": None,
    **REDUNDANT_JOB_DATA,
}

MOCK_QPU_STATE_DATA = {
    "block_durations": [],
    "gate_events": [],
    "qpu_fov": {"xmin": None, "xmax": None, "ymin": None, "ymax": None},
    "atoms": [],
    "slm_zone": [],
    "aod_moves": [],
}

MOCK_SIM_LOGS = [
    {"atom_id": 0, "block_id": 0, "action_type": "TrapSLM", "time": 0, "duration": 0},
    {
        "atom_id": 0,
        "block_id": 0,
        "action_type": "TrapAOD",
        "time": 0,
        "duration": 31.024984394500784,
    },
    {
        "atom_id": 0,
        "block_id": 0,
        "action_type": "DropAOD",
        "time": 31.024984394500784,
        "duration": 0,
    },
]

RESULTS_DATA_QUERA = {
    "backend": "cirq",
    "flairVisualVersion": "0.1.4",
    "logs": MOCK_SIM_LOGS,
    "atomAnimationState": MOCK_QPU_STATE_DATA,
    **REDUNDANT_JOB_DATA,
}


@pytest.fixture
def valid_qasm2():
    """Valid OpenQASM 2 string with measurement."""
    return """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c0[1];
    creg c1[1];
    swap q[0],q[1];
    measure q[0] -> c0[0];
    measure q[1] -> c1[0];
    """


@pytest.fixture
def qasm2_no_meas():
    """Valid OpenQASM 2 string without mesurement."""
    return """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    swap q[0],q[1];
    """


class MockClient:
    """Mock client for testing."""

    @property
    def session(self):
        """Mock session property."""
        session = MagicMock()
        session.api_key = "abc123"
        return session

    @property
    def _user_metadata(self):
        """Mock user metadata property."""
        return {"organization": "qbraid", "role": "guest"}

    def search_devices(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Returns a list of devices matching the given query."""
        if query.get("status") == "Bad status":
            raise QuantumServiceRequestError("No devices found matching given criteria")
        if query.get("provider") == "qBraid" or query.get("qbraid_id") == "qbraid_qir_simulator":
            return [DEVICE_DATA_QIR]
        if query.get("provider") == "QuEra" or query.get("qbraid_id") == "quera_qasm_simulator":
            return [DEVICE_DATA_QUERA]
        if query.get("vendor") == "qBraid":
            return [DEVICE_DATA_QIR, DEVICE_DATA_QUERA]
        return []

    def get_device(self, qbraid_id: Optional[str] = None, **kwargs):
        """Returns the device with the given ID."""
        if qbraid_id == "qbraid_qir_simulator":
            return DEVICE_DATA_QIR
        if qbraid_id == "quera_qasm_simulator":
            return DEVICE_DATA_QUERA
        raise QuantumServiceRequestError("No devices found matching given criteria")

    def create_job(self, data: dict[str, Any]) -> dict[str, Any]:
        """Creates a new quantum job with the given data."""
        device_id = data.get("qbraidDeviceId")
        if device_id == "qbraid_qir_simulator":
            job_data = JOB_DATA_QIR.copy()
            return job_data
        if device_id == "quera_qasm_simulator":
            job_data = JOB_DATA_QUERA.copy()
            return job_data
        raise QuantumServiceRequestError("Failed to create job")

    @staticmethod
    def _extract_device_id(job_id: str) -> str:
        """Extracts the device ID from the given job ID."""
        try:
            return job_id.split("-")[0]
        except IndexError as err:
            raise ValueError("Invalid job ID format") from err

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Returns the quantum job with the given ID."""
        device_id = self._extract_device_id(job_id)
        if device_id == "qbraid_qir_simulator":
            return JOB_DATA_QIR
        if device_id == "quera_qasm_simulator":
            return JOB_DATA_QUERA
        raise QuantumServiceRequestError("No jobs found matching given criteria")

    def get_job_results(self, job_id: str) -> dict[str, Any]:
        """Returns the results of the quantum job with the given ID."""
        device_id = self._extract_device_id(job_id)
        if device_id == "qbraid_qir_simulator":
            results_data = RESULTS_DATA_QIR.copy()
            return results_data
        if device_id == "quera_qasm_simulator":
            results_data = RESULTS_DATA_QUERA.copy()
            return results_data
        raise QuantumServiceRequestError("Failed to retrieve job results")


class MockDevice(QuantumDevice):
    """Mock basic device for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def status(self):
        raise NotImplementedError

    def submit(self, *args, **kwargs):
        raise NotImplementedError


@pytest.fixture
def mock_client():
    """Mock client for testing."""
    return MockClient()


@pytest.fixture
def mock_provider(mock_client):
    """Mock provider for testing."""
    return QbraidProvider(client=mock_client)


@pytest.fixture
def mock_profile():
    """Mock profile for testing."""
    return TargetProfile(
        device_id="qbraid_qir_simulator",
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=42,
        program_spec=QbraidProvider._get_program_spec("pyqir", "qbraid_qir_simulator"),
        noise_models=[NoiseModel.Ideal],
    )


@pytest.fixture
def mock_quera_profile():
    """Mock profile for testing."""
    return TargetProfile(
        device_id="quera_qasm_simulator",
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=64,
        program_spec=QbraidProvider._get_program_spec("qasm2", "quera_qasm_simulator"),
    )


@pytest.fixture
def mock_scheme():
    """Mock conversion scheme for testing."""
    conv1 = Conversion("alice", "bob", lambda x: x + 1)
    conv2 = Conversion("bob", "charlie", lambda x: x - 1)
    graph = ConversionGraph(conversions=[conv1, conv2])
    scheme = ConversionScheme(conversion_graph=graph)
    return scheme


@pytest.fixture
def mock_qbraid_device(mock_profile, mock_scheme, mock_client):
    """Mock QbraidDevice for testing."""
    return QbraidDevice(profile=mock_profile, client=mock_client, scheme=mock_scheme)


@pytest.fixture
def mock_quera_device(mock_quera_profile, mock_client):
    """Mock QuEra simulator device for testing."""
    return QbraidDevice(profile=mock_quera_profile, client=mock_client)


@pytest.fixture
def mock_basic_device(mock_profile):
    """Generic mock device for testing."""
    return MockDevice(profile=mock_profile)


@pytest.fixture
def pyqir_module() -> Module:
    """Returns a one-qubit PyQIR module with Hadamard gate and measurement."""
    bell = SimpleModule("test_qir_program", num_qubits=1, num_results=1)
    qis = BasicQisBuilder(bell.builder)

    qis.h(bell.qubits[0])
    qis.mz(bell.qubits[0], bell.results[0])

    return bell._module


def counts_to_measurements(counts: dict[str, Any]) -> np.ndarray:
    """Convert counts dictionary to measurements array."""
    measurements = []
    for state, count in counts.items():
        measurements.extend([list(map(int, state))] * count)
    return np.array(measurements, dtype=int)


def is_uniform_comput_basis(array: np.ndarray) -> bool:
    """
    Check if each measurement (row) in the array represents a uniform computational basis
    state, i.e., for each shot, that qubit measurements are either all |0⟩s or all |1⟩s.

    Args:
        array (np.ndarray): A 2D numpy array where each row represents a measurement shot,
                            and each column represents a qubit's state in that shot.

    Returns:
        bool: True if every measurement is in a uniform computational basis state
              (all |0⟩s or all |1⟩s). False otherwise.

    Raises:
        ValueError: If the given array is not 2D.
    """
    if array.ndim != 2:
        raise ValueError("The input array must be 2D.")

    for shot in array:
        # Check if all qubits in the shot are measured as |0⟩ or all as |1⟩
        if not (np.all(shot == 0) or np.all(shot == 1)):
            return False
    return True


def uniform_state_circuit(
    num_qubits: Optional[int] = None, measure: Optional[bool] = True
) -> cirq.Circuit:
    """
    Creates a Cirq circuit where all qubits are entangled to uniformly be in
    either |0⟩ or |1⟩ states upon measurement.

    This circuit initializes the first qubit in a superposition state using a
    Hadamard gate and then entangles all other qubits to this first qubit using
    CNOT gates. This ensures all qubits collapse to the same state upon measurement,
    resulting in either all |0⟩s or all |1⟩s uniformly across different executions.

    Args:
        num_qubits (optional, int): The number of qubits in the circuit. If not provided,
                                    a default random number between 10 and 20 is used.
        measure (optional, bool): Whether to measure the qubits at the end of the circuit.

    Returns:
        cirq.Circuit: The resulting circuit where the measurement outcome of all qubits is
                      either all |0⟩s or all |1⟩s.

    Raises:
        ValueError: If the number of qubits provided is less than 1.
    """
    if num_qubits is not None and num_qubits < 1:
        raise ValueError("Number of qubits must be at least 1.")

    num_qubits = num_qubits or random.randint(10, 20)

    qubits = [cirq.LineQubit(i) for i in range(num_qubits)]

    circuit = cirq.Circuit()

    circuit.append(cirq.H(qubits[0]))

    for qubit in qubits[1:]:
        circuit.append(cirq.CNOT(qubits[0], qubit))

    if measure:
        circuit.append(cirq.measure(*qubits, key="result"))

    return circuit


@pytest.fixture
def cirq_uniform():
    """Cirq circuit used for testing."""
    return uniform_state_circuit


def test_provider_equality(mock_provider, mock_client):
    """Test equality of provider instances."""
    assert mock_provider == QbraidProvider(client=mock_client)
    assert mock_provider != mock_client


def test_qir_simulator_workflow(mock_provider, cirq_uniform):
    """Test qir simulator qbraid device job submission and result retrieval."""
    circuit = cirq_uniform(num_qubits=5)
    num_qubits = len(circuit.all_qubits())

    provider = mock_provider
    device = provider.get_device("qbraid_qir_simulator")

    shots = 10
    job = device.run(circuit, shots=shots)
    assert isinstance(job, QbraidJob)
    assert job.is_terminal_state()

    batch_job = device.run([circuit], shots=shots, noise_model=NoiseModel.Ideal)
    assert isinstance(batch_job, list)
    assert all(isinstance(job, QbraidJob) for job in batch_job)

    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, QbraidQirSimulatorResultData)
    assert repr(result.data).startswith("QbraidQirSimulatorResultData")
    assert result.success
    assert result.job_id == JOB_DATA_QIR["qbraidJobId"]
    assert result.device_id == JOB_DATA_QIR["qbraidDeviceId"]

    counts = result.data.get_counts()
    probabilities = result.data.get_probabilities()
    assert len(counts) == len(probabilities) == 2
    assert sum(probabilities.values()) == 1.0
    assert is_uniform_comput_basis(result.data.measurements)

    assert result.details["shots"] == shots
    assert result.details["metadata"]["circuitNumQubits"] == num_qubits
    assert isinstance(result.details["timeStamps"]["executionDuration"], int)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert result.measurement_counts() == counts
        assert is_uniform_comput_basis(result.measurements())


def test_queara_simulator_workflow(mock_provider, cirq_uniform, qasm2_no_meas):
    """Test queara simulator job submission and result retrieval."""
    circuit = cirq_uniform(num_qubits=5, measure=False)
    num_qubits = len(circuit.all_qubits())

    provider = mock_provider
    device = provider.get_device("quera_qasm_simulator")

    shots = 10
    job = device.run(circuit, shots=shots)
    assert isinstance(job, QbraidJob)
    assert job.is_terminal_state()

    device._target_spec = None
    device.transform = lambda x: {"openQasm": x}
    batch_job = device.run([qasm2_no_meas], shots=shots)
    assert isinstance(batch_job, list)
    assert all(isinstance(job, QbraidJob) for job in batch_job)

    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, QuEraQasmSimulatorResultData)
    assert repr(result.data).startswith("QuEraQasmSimulatorResultData")
    assert result.success
    assert result.job_id == JOB_DATA_QUERA["qbraidJobId"]
    assert result.device_id == JOB_DATA_QUERA["qbraidDeviceId"]

    counts = result.data.get_counts()
    probabilities = result.data.get_probabilities()
    assert len(counts) == len(probabilities) == 2
    assert sum(probabilities.values()) == 1.0
    assert result.data.measurements is None
    assert result.data.flair_visual_version == RESULTS_DATA_QUERA["flairVisualVersion"]
    assert result.data.backend == RESULTS_DATA_QUERA["backend"]
    assert result.data._atom_animation_state == MOCK_QPU_STATE_DATA

    logs = result.data.get_logs()
    assert isinstance(logs, DataFrame)

    assert result.details["shots"] == shots
    assert result.details["metadata"]["circuitNumQubits"] == num_qubits
    assert isinstance(result.details["timeStamps"]["executionDuration"], int)


def test_run_forbidden_kwarg(mock_provider):
    """Test that invoking run method with forbidden kwarg raises value error."""
    circuit = Mock()
    provider = mock_provider
    device = provider.get_device("qbraid_qir_simulator")

    with pytest.raises(ValueError):
        device.run(circuit, shots=10, num_qubits=5)


def test_device_update_scheme(mock_qbraid_device):
    """Test updating ConversionScheme."""
    graph = mock_qbraid_device.scheme.conversion_graph.copy()
    new_conversion = Conversion("charlie", "alice", lambda x: x)
    graph.add_conversion(new_conversion)

    assert graph != mock_qbraid_device.scheme.conversion_graph

    mock_qbraid_device.update_scheme(conversion_graph=graph)

    assert graph == mock_qbraid_device.scheme.conversion_graph


def test_device_noisey_run_raises_for_unsupported(mock_qbraid_device):
    """Test raising exception when noise model is not supported."""
    with pytest.raises(ValueError):
        mock_qbraid_device.run(Mock(), noise_model=NoiseModel.AmplitudeDamping)


def test_device_transform(pyqir_module, mock_qbraid_device):
    """Test transform method on OpenQASM 2 string."""
    assert mock_qbraid_device.transform(pyqir_module) == {"bitcode": pyqir_module.bitcode}


def test_device_extract_qasm(valid_qasm2, mock_qbraid_device):
    """Test that the extracting OpenQASM representation function
    returns qasm2 string for qasm2 program spec."""
    assert (
        mock_qbraid_device._extract_qasm_rep(valid_qasm2, ProgramSpec(str, "qasm2")) == valid_qasm2
    )


def test_device_extract_qasm_rep_none(mock_qbraid_device):
    """Test that the extracting OpenQASM representation function returns
    None if no OpenQASM conversion is supported from given program type."""
    try:
        alias = "unittest"
        register_program_type(Mock, alias, overwrite=True)
        assert mock_qbraid_device._extract_qasm_rep(None, ProgramSpec(Mock, alias)) is None
    finally:
        unregister_program_type(alias)


def test_device_run_raises_for_protected_kwargs(valid_qasm2, mock_qbraid_device):
    """Test raising exception when run method is invoked with protected kwargs."""
    kwargs = {"openQasm": valid_qasm2}
    with pytest.raises(ValueError):
        mock_qbraid_device.run(valid_qasm2, **kwargs)


def test_provider_initialize_client_raises_for_multiple_auth_params():
    """Test raising exception when initializing client if provided
    both an api key and a client object."""
    with pytest.raises(ValueError):
        QbraidProvider(api_key="abc123", client=MockClient())


def test_provider_resource_not_found_error_for_bad_api_key():
    """Test raising ResourceNotFoundError when the client fails to authenticate."""
    provider = QbraidProvider(api_key="abc123")
    with pytest.raises(ResourceNotFoundError):
        _ = provider.client


@patch("qbraid.runtime.native.provider.QuantumClient")
def test_provider_client_from_valid_api_key(client):
    """Test a valid API key."""
    mock_client = MockClient()
    client.return_value = mock_client
    provider = QbraidProvider(api_key="abc123")
    assert provider.client == mock_client


def test_provider_get_devices(mock_client):
    """Test getting devices from the client."""
    client = mock_client
    provider = QbraidProvider(client=client)
    devices = provider.get_devices(qbraid_id="qbraid_qir_simulator")
    assert len(devices) == 1
    assert devices[0].id == "qbraid_qir_simulator"


def test_provider_get_cached_devices(mock_client, monkeypatch):
    """Test getting devices from the cache."""
    monkeypatch.setenv("DISABLE_CACHE", "0")

    client = mock_client
    provider = QbraidProvider(client=client)
    client.search_devices = Mock()
    client.search_devices.return_value = [DEVICE_DATA_QIR]

    _ = provider.get_devices(qbraid_id="qbraid_qir_simulator")

    # second call should be from cache
    _ = provider.get_devices(qbraid_id="qbraid_qir_simulator")
    client.search_devices.assert_called_once()

    provider.get_devices.cache_clear()


def test_provider_get_devices_post_cache_expiry(mock_client, monkeypatch):
    """Test that the cache entry is invalidated when the cache is too old."""
    monkeypatch.setenv("DISABLE_CACHE", "0")
    monkeypatch.setenv("_QBRAID_TEST_CACHE_CALLS", "1")

    client = mock_client
    provider = QbraidProvider(client=client)
    client.search_devices = Mock()
    client.search_devices.return_value = [DEVICE_DATA_QIR]

    init_time = time.time()
    device_ttl = 120
    _ = provider.get_devices(qbraid_id="qbraid_qir_simulator")

    # second call should not come from cache
    with patch("time.time", return_value=init_time + device_ttl + 5):
        _ = provider.get_devices(qbraid_id="qbraid_qir_simulator")
    assert client.search_devices.call_count == 2


def test_provider_get_devices_bypass_cache(mock_client, monkeypatch):
    """Test that the cache is bypassed when the bypass_cache flag is set."""
    monkeypatch.setenv("DISABLE_CACHE", "0")
    monkeypatch.setenv("_QBRAID_TEST_CACHE_CALLS", "1")

    client = mock_client
    provider = QbraidProvider(client=client)
    client.search_devices = Mock()
    client.search_devices.return_value = [DEVICE_DATA_QIR]

    with cache_disabled(provider):
        assert provider.__cache_disabled is True  # pylint: disable=no-member
        _ = provider.get_devices(qbraid_id="qbraid_qir_simulator")

    assert provider.__cache_disabled is False  # pylint: disable=no-member
    assert client.search_devices.call_count == 1
    provider.get_devices.cache_clear()


def test_provider_search_devices_raises_for_bad_client():
    """Test raising ResourceNotFoundError when the client fails to authenticate."""
    provider = QbraidProvider(client=MockClient())
    with pytest.raises(ResourceNotFoundError):
        provider.get_devices(qbraid_id="qbraid_qir_simulator", status="Bad status")


def test_provider_program_spec_none():
    """Test getting program spec when it is None."""
    assert QbraidProvider._get_program_spec(None, "device_id") is None


def test_device_queue_depth_raises(mock_basic_device):
    """Test raising exception when queue depth is unavailable."""
    with pytest.raises(ResourceNotFoundError):
        mock_basic_device.queue_depth()


def test_device_queue_depth(mock_qbraid_device):
    """Test getting queue depth."""
    assert mock_qbraid_device.queue_depth() == 0


def test_device_status(mock_qbraid_device, mock_profile, mock_client):
    """Test getting device status."""
    assert mock_qbraid_device.status() == DeviceStatus.ONLINE
    DEVICE_DATA_QIR["status"] = None
    with pytest.raises(QbraidRuntimeError):
        device = QbraidDevice(profile=mock_profile, client=mock_client)
        device.status()


def test_try_extracting_info_exception_handling(caplog, mock_qbraid_device):
    """Test try_extracting_info exception handling."""
    obj = mock_qbraid_device

    def problematic_func():
        raise ValueError("This is a test error")

    caplog.set_level(logging.INFO)
    result = obj.try_extracting_info(problematic_func, "Error encountered")
    assert result is None
    assert (
        "Error encountered: This is a test error. Field will be omitted in job metadata."
        in caplog.text
    )


def test_device_metadata(mock_basic_device):
    """Test getting device metadata."""
    metadata = mock_basic_device.metadata()
    assert metadata["device_id"] == "qbraid_qir_simulator"
    assert metadata["simulator"] is True
    assert metadata["num_qubits"] == 42


def test_failed_circuit_conversion(mock_basic_device, mock_scheme):
    """Test raising exception when circuit conversion fails."""

    class FailMockTypeA:
        """Mock type for testing."""

    class FailMockTypeB:
        """Mock type for testing."""

    fake_spec = ProgramSpec(FailMockTypeA, alias="alice")
    mock_basic_device._target_spec = ProgramSpec(FailMockTypeB, alias="charlie")
    mock_basic_device._scheme = mock_scheme
    mock_input = FailMockTypeA()
    with pytest.raises(QbraidRuntimeError):
        mock_basic_device.transpile(mock_input, fake_spec)

    mock_basic_device._target_spec = None
    assert mock_basic_device.transpile(mock_input, fake_spec) == mock_input

    unregister_program_type("alice")
    unregister_program_type("charlie")


def test_wrong_type_conversion(mock_basic_device):
    """Test raising exception when circuit conversion fails due to wrong type."""

    class MockTypeA:
        """Mock type for testing."""

        def __init__(self, x):
            self.x = x

        def __add__(self, other):
            return MockTypeA(self.x + other.x)

        def __eq__(self, other):
            return self.x == other.x

    class MockTypeB:
        """Mock type for testing."""

        def __init__(self, x):
            self.x = x

        def __add__(self, other):
            return MockTypeB(self.x + other.x)

        def __eq__(self, other):
            return self.x == other.x

    conv1 = Conversion("alice", "charlie", lambda x: x + MockTypeA(1))
    graph = ConversionGraph(conversions=[conv1])
    scheme = ConversionScheme(conversion_graph=graph)

    fake_spec = ProgramSpec(MockTypeA, alias="alice", overwrite=True)
    mock_basic_device._target_spec = ProgramSpec(MockTypeB, alias="charlie", overwrite=True)
    mock_basic_device._scheme = scheme
    mock_input = MockTypeA(1)
    with pytest.raises(CircuitConversionError):
        mock_basic_device.transpile(mock_input, fake_spec)

    unregister_program_type("alice")
    unregister_program_type("charlie")


class FakeSession:
    """Mock session for testing."""

    def save_config(self, **kwargs):  # pylint: disable=unused-argument
        """Mock save configuration."""
        return None


class FakeClient:
    """Mock client for testing."""

    def __init__(self, api_key=None):  # pylint: disable=unused-argument
        self.session = FakeSession()

    def get_device(self, qbraid_id):
        """Mock get device."""
        raise ValueError("Device not found")


def test_save_config():
    """Test saving configuration."""
    provider = QbraidProvider(client=FakeClient())
    try:
        provider.save_config(param1="value1", param2="value2")
    except Exception:  # pylint: disable=broad-except
        pytest.fail("save_config raised an exception unexpectedly")


def test_get_device_fail():
    """Test raising exception when device is not found."""
    provider = QbraidProvider(client=FakeClient())
    with pytest.raises(ResourceNotFoundError):
        provider.get_device("qbraid_qir_simulator")


def test_set_options(mock_qbraid_device: QbraidDevice):
    """Test updating the default runtime options."""
    default_options = {"transpile": True, "transform": True, "validate": True}
    assert dict(mock_qbraid_device._options) == default_options

    mock_qbraid_device.set_options(transform=False)
    updated_options = default_options.copy()
    updated_options["transform"] = False
    assert dict(mock_qbraid_device._options) == updated_options


def test_transform_to_ir_from_spec(mock_basic_device: MockDevice, pyqir_module: Module):
    """Test transforming to run input to given IR from target profile program spec."""
    run_input_transformed = mock_basic_device.transform(pyqir_module)
    assert isinstance(run_input_transformed, dict)
    assert isinstance(run_input_transformed.get("bitcode"), bytes)

    mock_basic_device._target_spec = None
    run_input_transformed = mock_basic_device.transform(pyqir_module)
    assert isinstance(run_input_transformed, Module)


def test_set_options_raises_for_bad_key(mock_basic_device: MockDevice):
    """Test that the set options method raises AttributeError for key
    not already included in options."""
    with pytest.raises(AttributeError):
        mock_basic_device.set_options(bad_key=True)


def test_estimate_cost_success(mock_qbraid_device):
    """Test estimate_cost returns the correct cost."""
    mock_core_client = Mock()
    mock_core_client.estimate_cost.return_value = 8.75
    mock_qbraid_device._client = mock_core_client

    cost = mock_qbraid_device.estimate_cost(shots=100, execution_time=1.1)
    assert cost == 8.75
    mock_core_client.estimate_cost.assert_called_once_with(mock_qbraid_device.id, 100, 1.1)


@pytest.mark.parametrize(
    "shots, execution_time",
    [
        (None, None),
        (-1, 1.0),
        (100, -1.0),
        (0, 0),
        (None, 0),
        (0, None),
    ],
)
def test_estimate_cost_raises_for_invalid_args(mock_qbraid_device, shots, execution_time):
    """Test that estimate_cost raises ValueError for invalid arguments."""
    with pytest.raises(ValueError):
        mock_qbraid_device.estimate_cost(shots=shots, execution_time=execution_time)


def test_estimate_cost_resource_not_found_error(mock_qbraid_device):
    """Test estimate_cost raises ResourceNotFoundError if the core client fails."""
    mock_core_client = Mock()
    mock_core_client.estimate_cost.side_effect = QuantumServiceRequestError("Request failed")
    mock_qbraid_device._client = mock_core_client

    with pytest.raises(QbraidRuntimeError):
        mock_qbraid_device.estimate_cost(shots=100, execution_time=10.0)


def test_validate_quera_device_qasm_validator(mock_quera_device, valid_qasm2):
    """Test that validate method raises ValueError for QASM programs with measurements."""
    with pytest.raises(ProgramValidationError):
        mock_quera_device.validate(valid_qasm2)


@pytest.mark.parametrize(
    "status, status_text",
    [("FAILED", "Custom status text"), (JobStatus.FAILED, "Different custom status text")],
)
def test_runtime_job_model_from_dict_custom_status(status, status_text):
    """Test creating a RuntimeJobModel with custom status."""
    job_data = JOB_DATA_QIR.copy()
    job_data["status"] = status
    job_data["statusText"] = status_text

    model = RuntimeJobModel.from_dict(job_data)

    assert model.status == JobStatus.FAILED.value
    assert model.status_text == status_text


def test_construct_aux_payload_no_spec(mock_quera_device, qasm2_no_meas):
    """Test constructing auxiliary payload without a predefined program spec."""
    aux_payload = mock_quera_device._construct_aux_payload(qasm2_no_meas)
    assert len(aux_payload) == 3
    assert aux_payload["openQasm"] == qasm2_no_meas
    assert aux_payload["circuitNumQubits"] == 2
    assert aux_payload["circuitDepth"] == 1


@pytest.fixture
def mock_qbraid_client():
    """Mock client for testing."""
    client = Mock()
    client._user_metadata = {"organization": "qbraid", "role": "guest"}
    client.session.api_key = "mock_api_key"
    return client


@patch("builtins.hash", autospec=True)
def test_hash_method_creates_and_returns_hash(mock_hash, mock_qbraid_client):
    """Test that the hash method creates and returns a hash."""
    mock_hash.return_value = 8888
    provider_instance = QbraidProvider(client=mock_qbraid_client)
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    expected_organization_role = "qbraid-guest"
    mock_hash.assert_called_once_with(
        ("QbraidProvider", "mock_api_key", expected_organization_role)
    )
    assert result == 8888
    assert provider_instance._hash == 8888


def test_hash_method_returns_existing_hash(mock_qbraid_client):
    """Test that the hash method returns an existing hash."""
    provider_instance = QbraidProvider(client=mock_qbraid_client)
    provider_instance._hash = 5678
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    assert result == 5678

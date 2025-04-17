# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for QiskitProvider class

"""
import random
import warnings
from collections import OrderedDict
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.exceptions import QiskitError
from qiskit.primitives.primitive_job import PrimitiveJob
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, RuntimeJob
from qiskit_ibm_runtime.exceptions import IBMNotAuthorizedError, RuntimeInvalidStateError
from qiskit_ibm_runtime.qiskit_runtime_service import QiskitBackendNotFoundError

from qbraid.programs import NATIVE_REGISTRY, ExperimentType, ProgramSpec
from qbraid.runtime import DeviceStatus, GateModelResultData, JobStateError, Result, TargetProfile
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.ibm import QiskitBackend, QiskitJob, QiskitRuntimeProvider
from qbraid.runtime.ibm.result_builder import QiskitGateModelResultBuilder

try:
    from qiskit.providers.models.backendconfiguration import QasmBackendConfiguration

except ModuleNotFoundError:
    from qiskit_ibm_runtime.models.backend_configuration import QasmBackendConfiguration

FIXTURE_COUNT = sum(key in NATIVE_REGISTRY for key in ["qiskit", "braket", "cirq"])

FAKE_BASIS_GATES = ["u1", "u2", "u3", "cx"]


class FakeDevice(GenericBackendV2):
    """A test Qiskit device."""

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        num_qubits,
        local=True,
        simulator=True,
        operational=True,
        status_msg="active",
        **kwargs,
    ):
        super().__init__(num_qubits)
        self._num_qubits = num_qubits
        self._operational = operational
        self._status_msg = status_msg
        self._local = local
        self._simulator = simulator
        self._instance = kwargs.get("instance", None)

    def status(self):
        """Return the status of the backend."""
        status_obj = SimpleNamespace()
        status_obj.operational = self._operational
        status_obj.status_msg = self._status_msg

        # dummy value proportional to num_qubits
        status_obj.pending_jobs = 0 if self._local else random.randint(1, 100)
        return status_obj

    def configuration(self):
        """Return the configuration of the backend."""
        return QasmBackendConfiguration(
            backend_name="fake_backend",
            backend_version="1.0",
            n_qubits=self._num_qubits,
            basis_gates=FAKE_BASIS_GATES,
            gates=[],
            local=self._local,
            simulator=self._simulator,
            conditional=False,
            open_pulse=False,
            memory=True,
            max_shots=8192,
            coupling_map=None,
        )


class FakeService:
    """Fake Qiskit runtime service for testing."""

    def backend(self, backend_name, instance=None):
        """Return fake backend."""
        for backend in self.backends(instance=instance):
            if backend_name == backend.name:
                return backend
        raise QiskitBackendNotFoundError("No backend matches the criteria.")

    def backends(self, **kwargs):  # pylint: disable=unused-argument
        """Return fake Qiskit backend."""
        return [FakeDevice(num_qubits=n, **kwargs) for n in [5, 20]]

    def backend_names(self, **kwargs):
        """Return fake backend names."""
        return [backend.name for backend in self.backends(**kwargs)]

    def least_busy(self, **kwargs):
        """Return the least busy backend based on the number of pending jobs."""
        backends = self.backends(**kwargs)
        return min(backends, key=lambda backend: backend.status().pending_jobs)

    def job(self, job_id):  # pylint: disable=unused-argument
        """Return fake job."""
        return MagicMock(spec=RuntimeJob)


def _create_backend_fixture(service: FakeService, local: bool, simulator: bool) -> QiskitBackend:
    """Create a Qiskit backend fixture."""
    backend = service.backends(local=local, simulator=simulator)[0]
    program_spec = ProgramSpec(QuantumCircuit)
    profile = TargetProfile(
        device_id=backend.name,
        local=local,
        simulator=simulator,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=backend.num_qubits,
        program_spec=program_spec,
        provider_name="IBM",
    )
    return QiskitBackend(profile, service)


@pytest.fixture
def fake_service():
    """Return a fake Qiskit runtime service."""
    return FakeService()


@pytest.fixture
def fake_device(fake_service):
    """Return a fake local simulator backend."""
    return _create_backend_fixture(fake_service, local=True, simulator=True)


def test_provider_initialize_service():
    """Test getting IBMQ provider using qiskit_ibm_provider package."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = Mock(spec=QiskitRuntimeService)
        provider = QiskitRuntimeProvider(token="test_token", channel="test_channel")
        assert isinstance(provider.runtime_service, QiskitRuntimeService)
        assert provider.token == "test_token"
        assert provider.channel == "test_channel"
        assert provider.runtime_service == mock_runtime_service.return_value


def test_provider_save_config(fake_service):
    """Test saving the IBM account configuration to disk."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = fake_service
        provider = QiskitRuntimeProvider(
            token="fake_token", instance="ibm-q/open/main", channel="fake_channel"
        )

        provider.save_config(
            token="fake_token", instance="ibm-q/open/main", channel="fake_channel", overwrite=False
        )
        mock_runtime_service.save_account.assert_called_once_with(
            token="fake_token", instance="ibm-q/open/main", channel="fake_channel", overwrite=False
        )

        provider.save_config()
        mock_runtime_service.save_account.assert_called_with(
            token="fake_token", instance="ibm-q/open/main", channel="fake_channel", overwrite=True
        )


@pytest.mark.parametrize(
    "local,simulator,num_qubits",
    [
        (True, True, 20),
        (False, True, 5),
        (False, False, 5),
    ],
)
def test_provider_build_runtime_profile(local, simulator, num_qubits):
    """Test building runtime profile for Qiskit backend."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = FakeService()
        backend = FakeDevice(num_qubits, local=local, simulator=simulator)
        provider = QiskitRuntimeProvider(token="test_token", channel="test_channel")
        profile = provider._build_runtime_profile(backend)
        assert profile["device_id"] == f"generic_backend_{num_qubits}q"
        assert profile["simulator"] == simulator
        assert profile["local"] == local
        assert profile["num_qubits"] == num_qubits
        assert profile["max_shots"] == 8192
        assert profile.basis_gates == set(FAKE_BASIS_GATES)

        qiskit_backend = QiskitBackend(profile, mock_runtime_service())
        assert isinstance(qiskit_backend, QiskitBackend)
        assert qiskit_backend.profile == profile


def test_provider_get_devices(fake_service):
    """Test getting a backend from the runtime service."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = fake_service
        provider = QiskitRuntimeProvider(token="test_token", channel="test_channel")
        devices = provider.get_devices()
        assert len(devices) == 2
        assert all(isinstance(device, QiskitBackend) for device in devices)

        device = devices[0]
        device_copy = provider.get_device(device.id)
        assert device.id == device_copy.id
        assert str(device) == f"QiskitBackend('{device.id}')"


@pytest.mark.parametrize("local", [True, False])
def test_provider_least_busy(fake_service, local):
    """Test getting a backend from the runtime service, both local and non-local."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService") as mock_provider_service:
        mock_provider_service.return_value = fake_service
        provider = QiskitRuntimeProvider(token="test_token", channel="test_channel")

        least_busy = provider.least_busy(local=local)
        least_busy._backend = FakeDevice(5, local=local)

        assert least_busy.queue_depth() == 0 if local else least_busy.queue_depth() > 0


@pytest.mark.parametrize(
    "operational,local,status_msg,expected_status",
    [
        (True, True, "active", DeviceStatus.ONLINE),
        (True, False, "active", DeviceStatus.ONLINE),
        (True, False, "not active", DeviceStatus.UNAVAILABLE),
        (False, False, None, DeviceStatus.OFFLINE),
    ],
)
def test_device_status(fake_service, operational, local, status_msg, expected_status):
    """Test getting a backend from the runtime service, both local and non-local."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService") as mock_provider_service:
        mock_provider_service.return_value = fake_service
        provider = QiskitRuntimeProvider(token="test_token", channel="test_channel")
        params = {"operational": operational, "local": local, "status_msg": status_msg}
        device = provider.get_devices(**params)[0]
        device._backend = FakeDevice(device.num_qubits, **params)
        assert device.status() == expected_status


@pytest.mark.parametrize("circuit_meas", range(FIXTURE_COUNT), indirect=True)
def test_device_run(fake_device, circuit_meas):
    """Test run method from wrapped fake Qiskit backends"""
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=RuntimeWarning)
        qbraid_job = fake_device.run(circuit_meas, shots=10)

    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, PrimitiveJob)


def test_device_run_batch(fake_device, run_inputs):
    """Test run method from wrapped fake Qiskit backends"""
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=RuntimeWarning)
        qbraid_job = fake_device.run(run_inputs, shots=10)

    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, PrimitiveJob)


@pytest.fixture
def mock_service():
    """Fixture to create a mock QiskitRuntimeService."""
    service = MagicMock(spec=QiskitRuntimeService)
    service.job.return_value = MagicMock(spec=RuntimeJob)
    return service


def test_job_initialize_from_service(mock_service):
    """Test successful job retrieval with a provided service.

    Args:
        mock_service (MagicMock): A mocked service passed as a fixture.

    Tests that QiskitJob retrieves a job using a provided mock service and verifies
    that the job method is called exactly once with the correct job ID.
    """
    job_id = "test_job_id"
    job = QiskitJob(job_id, service=mock_service)
    assert job._job is not None
    mock_service.job.assert_called_once_with(job_id)


def test_job_initialize_service_from_device(mock_service):
    """Test job retrieval when service is provided via the device attribute."""
    mock_device = MagicMock()
    mock_device._service = mock_service

    job_id = "test_job_id"
    job = QiskitJob(job_id, device=mock_device)

    assert job._job is not None
    mock_service.job.assert_called_once_with(job_id)


def test_job_service_initialization():
    """Test job retrieval when initializing a new service."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService") as mock_service_class:
        mock_service = MagicMock(spec=QiskitRuntimeService)
        mock_service.job.return_value = MagicMock(spec=RuntimeJob)
        mock_service_class.return_value = mock_service
        job_id = "test_job_id"
        job = QiskitJob(job_id)
        assert job._job is not None
        mock_service.job.assert_called_once_with(job_id)


def test_job_service_initialization_failure():
    """Test handling of service initialization failure."""
    with patch(
        "qbraid.runtime.ibm.provider.QiskitRuntimeService", side_effect=IBMNotAuthorizedError
    ):
        job_id = "test_job_id"
        with pytest.raises(QbraidRuntimeError) as excinfo:
            QiskitJob(job_id)
        assert "Failed to initialize the quantum service." in str(excinfo.value)


def test_job_retrieval_failure(mock_service):
    """Test handling of job retrieval failure."""
    mock_service.job.side_effect = ConnectionError
    job_id = "test_job_id"
    with pytest.raises(QbraidRuntimeError) as excinfo:
        QiskitJob(job_id, service=mock_service)
    assert "Error retrieving job test_job_id" in str(excinfo.value)


@pytest.fixture
def mock_runtime_job():
    """Fixture to create a mock QiskitRuntimeJob object."""
    return MagicMock()


def test_job_queue_position(mock_runtime_job):
    """Test that the queue position of the job is correctly returned."""
    queue_position = 5
    mock_runtime_job.queue_position.return_value = queue_position

    job = QiskitJob(job_id="123", job=mock_runtime_job)
    assert job.queue_position() == queue_position


def test_cancel_job_in_terminal_state(mock_runtime_job):
    """Test attempting to cancel a job in a terminal state raises JobStateError."""
    job = QiskitJob(job_id="123", job=mock_runtime_job)
    job.is_terminal_state = MagicMock(return_value=True)  # Simulate terminal state

    with pytest.raises(JobStateError, match="Cannot cancel quantum job in non-terminal state."):
        job.cancel()


def test_cancel_job_success(mock_runtime_job):
    """Test successful cancellation of a non-terminal job."""
    job = QiskitJob(job_id="123", job=mock_runtime_job)
    job.is_terminal_state = MagicMock(return_value=False)
    mock_runtime_job.cancel.return_value = None

    assert job.cancel() is None


def test_cancel_job_fails_due_to_runtime_error(mock_runtime_job):
    """Test that cancellation fails with a RuntimeInvalidStateError and raises JobStateError."""
    mock_job = mock_runtime_job
    mock_job.cancel.side_effect = RuntimeInvalidStateError
    job = QiskitJob(job_id="123", job=mock_job)
    job.is_terminal_state = MagicMock(return_value=False)

    with pytest.raises(JobStateError):
        job.cancel()


@pytest.fixture
def mock_result_metadata():
    """Return a dictionary of mock result metadata."""
    return {
        "job_id": "123",
        "success": True,
        "backend_name": "fake_backend",
        "backend_version": "0.0.0",
    }


@pytest.fixture
def mock_runtime_result(mock_result_metadata):
    """Return a mock Qiskit result."""
    mock_result = Mock()
    mock_result.results = [Mock(), Mock()]
    meas1 = ["01"] * 9 + ["10"] + ["11"] * 4 + ["00"] * 6
    meas2 = ["0"] * 8 + ["1"] * 12
    mock_result.get_memory.side_effect = [meas1, meas2]
    mock_result.get_counts.side_effect = [{"01": 9, "10": 1, "11": 4, "00": 6}, {"0": 8, "1": 12}]
    mock_result.to_dict.return_value = mock_result_metadata
    return mock_result


def test_result_from_job(mock_runtime_job, mock_runtime_result, mock_result_metadata):
    """Test that result returns QiskitGateModelResultBuilder when the job is in a terminal state."""
    mock_job = QiskitJob(job_id="123", job=mock_runtime_job)
    mock_runtime_job.result.return_value = mock_runtime_result
    result = mock_job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert isinstance(result.data.get_counts(), dict)
    assert isinstance(result.data.measurements, np.ndarray)
    assert result.details.get("job_id") is None
    assert result.details.get("success") is None
    assert result.details.get("backend_name") == mock_result_metadata["backend_name"]
    assert result.details.get("backend_version") == mock_result_metadata["backend_version"]


def test_result_get_counts(mock_runtime_result):
    """Test getting raw counts from a Qiskit result."""
    qr = QiskitGateModelResultBuilder(mock_runtime_result)
    expected = {"01": 9, "10": 1, "11": 4, "00": 6}
    assert qr.get_counts() == expected


def test_result_format_measurements(mock_runtime_result):
    """Test formatting measurements into integers."""
    qr = QiskitGateModelResultBuilder(mock_runtime_result)
    memory_list = ["010", "111"]
    expected = [[0, 1, 0], [1, 1, 1]]
    assert qr._format_measurements(memory_list) == expected


def test_result_measurements_single_circuit(mock_runtime_result):
    """Test getting measurements from a single circuit."""
    qr = QiskitGateModelResultBuilder(mock_runtime_result)
    mock_runtime_result.results = [Mock()]
    expected = np.array([[0, 1]] * 9 + [[1, 0]] + [[1, 1]] * 4 + [[0, 0]] * 6)
    assert np.array_equal(qr.measurements(), expected)


def test_result_measurements_multiple_circuits(mock_runtime_result):
    """Test getting measurements from multiple circuits."""
    qr = QiskitGateModelResultBuilder(mock_runtime_result)
    expected_meas1 = np.array([[0, 1]] * 9 + [[1, 0]] + [[1, 1]] * 4 + [[0, 0]] * 6)
    expected_meas2 = np.array([[0, 0]] * 8 + [[0, 1]] * 12)
    expected = np.array([expected_meas1, expected_meas2])
    assert np.array_equal(qr.measurements(), expected)


@patch("builtins.hash", autospec=True)
def test_hash_method_creates_and_returns_hash(mock_hash):
    """Test that the __hash__ method creates and returns a hash value."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = Mock(spec=QiskitRuntimeService)
        provider_instance = QiskitRuntimeProvider(token="mock_token", channel="ibm_cloud")
        mock_hash.return_value = 12345
        result = provider_instance.__hash__()  # pylint: disable=unnecessary-dunder-call
        mock_hash.assert_called_once_with(("mock_token", "ibm_cloud"))
        assert result == 12345
        assert provider_instance._hash == 12345


def test_hash_method_returns_existing_hash():
    """Test that the hash method returns the existing hash value."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = Mock(spec=QiskitRuntimeService)
        provider_instance = QiskitRuntimeProvider(token="mock_token", channel="ibm_cloud")
        provider_instance._hash = 67890
        result = provider_instance.__hash__()  # pylint: disable=unnecessary-dunder-call
        assert result == 67890


def test_result_measurements_not_available(mock_runtime_result, caplog):
    """Test returning None and logging a warning when measurements are not available."""
    qr = QiskitGateModelResultBuilder(mock_runtime_result)
    mock_result = Mock()
    mock_result.results = qr._result.results
    mock_result.get_memory.side_effect = QiskitError("Test QiskitError message")
    qr._result = mock_result

    with caplog.at_level("WARNING"):
        result = qr.measurements()

    assert result is None
    assert "Memory states (measurements) data not available for this job" in caplog.text
    assert "Test QiskitError message" in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert (
        "Memory states (measurements) data not available for this job" in caplog.records[0].message
    )


def test_transform_run_input(fake_device):
    """Test that the transform method optimizes the circuit for the device."""
    circuit = QuantumCircuit(4)

    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(2, 3)
    circuit.measure_all()

    circuit_optimized_for_device = fake_device.transform(circuit)

    pm = generate_preset_pass_manager()

    fake_device.set_options(pass_manager=pm)

    circuit_optimized_default = fake_device.transform(circuit)

    default_ops = OrderedDict([("measure", 4), ("cx", 3), ("h", 1), ("barrier", 1)])
    optimized_ops = OrderedDict([("measure", 4), ("cx", 3), ("rz", 2), ("sx", 1), ("barrier", 1)])

    assert circuit.count_ops() == circuit_optimized_default.count_ops() == default_ops
    assert circuit_optimized_for_device.count_ops() == optimized_ops


def test_device_run_with_sampler(fake_device, qiskit_uniform):
    """Test that the device can run a circuit with a sampler."""
    shots = 10
    num_qubits = 2

    qbraid_job = fake_device.run(qiskit_uniform(num_qubits), shots=shots)
    assert isinstance(qbraid_job, QiskitJob)

    result = qbraid_job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert isinstance(result.data.get_counts(), dict)
    assert isinstance(result.data.measurements, np.ndarray)
    assert result.data.measurements.shape == (shots, 1)

    counts = result.data.get_counts()
    assert sum(counts.values()) == shots
    assert all(len(k) == num_qubits for k in counts.keys())

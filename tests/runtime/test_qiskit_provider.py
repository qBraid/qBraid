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
import time
import warnings
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.providers import Backend, Job
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.providers.models import QasmBackendConfiguration
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.qiskit_runtime_service import QiskitBackendNotFoundError

from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
from qbraid.runtime import DeviceActionType, DeviceType, JobStateError, TargetProfile
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.qiskit import QiskitBackend, QiskitJob, QiskitResult, QiskitRuntimeProvider

FIXTURE_COUNT = sum(key in NATIVE_REGISTRY for key in ["qiskit", "braket", "cirq"])


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
        return [GenericBackendV2(num_qubits=5), GenericBackendV2(num_qubits=20)]

    def backend_names(self, **kwargs):
        """Return fake backend names."""
        return [backend.name for backend in self.backends(**kwargs)]

    def least_busy(self, **kwargs):
        """Return least busy backend."""
        return random.choice(self.backends(**kwargs))

    def job(self, job_id):  # pylint: disable=unused-argument
        """Return fake job."""
        return


class FakeDevice(GenericBackendV2):
    """A test Qiskit device."""

    def __init__(self, num_qubits):
        super().__init__(num_qubits)
        self._num_qubits = num_qubits
        self._instance = None

    def configuration(self):
        """Return the configuration of the backend."""
        return QasmBackendConfiguration(
            backend_name="fake_backend",
            backend_version="1.0",
            n_qubits=self._num_qubits,
            basis_gates=["u1", "u2", "u3", "cx"],
            gates=[],
            local=True,
            simulator=False,
            conditional=False,
            open_pulse=False,
            memory=False,
            max_shots=8192,
            coupling_map=None,
        )


def ibm_devices():
    """Get list of wrapped ibm backends for testing."""
    provider = QiskitRuntimeProvider()
    backends = provider.get_devices(
        filters=lambda b: b.status().status_msg == "active", operational=True
    )
    return [backend.id for backend in backends]


def fake_ibm_devices():
    """Get list of fake wrapped ibm backends for testing"""
    service = FakeService()
    backends = service.backends()
    program_spec = ProgramSpec(QuantumCircuit)
    profiles = [
        TargetProfile(
            backend.name,
            DeviceType.LOCAL_SIMULATOR,
            DeviceActionType.OPENQASM,
            backend.num_qubits,
            program_spec,
        )
        for backend in backends
    ]
    return [QiskitBackend(profile, service) for profile in profiles]


@pytest.mark.parametrize("device", fake_ibm_devices())
def test_wrap_fake_provider(device):
    """Test wrapping fake Qiskit provider."""
    assert isinstance(device, QiskitBackend)
    assert isinstance(device._backend, Backend)


def test_queue_depth():
    """Test getting number of pending jobs for QiskitBackend."""
    ibm_device = fake_ibm_devices()[0]
    assert isinstance(ibm_device.queue_depth(), int)


@pytest.mark.parametrize("qbraid_device", fake_ibm_devices())
@pytest.mark.parametrize("circuit", range(FIXTURE_COUNT), indirect=True)
def test_run_fake_qiskit_device_wrapper(qbraid_device, circuit):
    """Test run method from wrapped fake Qiskit backends"""
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=RuntimeWarning)
        qbraid_job = qbraid_device.run(circuit, shots=10)

    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, Job)


@pytest.mark.parametrize("qbraid_device", fake_ibm_devices())
def test_run_fake_batch_qiskit_device_wrapper(qbraid_device, run_inputs):
    """Test run method from wrapped fake Qiskit backends"""
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=RuntimeWarning)
        qbraid_job = qbraid_device.run(run_inputs, shots=10)

    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, Job)


def test_qiskit_provider():
    """Test getting IBMQ provider using qiskit_ibm_provider package."""
    with patch("qbraid.runtime.qiskit.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = Mock(spec=QiskitRuntimeService)
        provider = QiskitRuntimeProvider(token="test_token", channel="test_channel")
        assert isinstance(provider.runtime_service, QiskitRuntimeService)
        assert provider.token == "test_token"
        assert provider.channel == "test_channel"
        assert provider.runtime_service == mock_runtime_service.return_value


def test_get_service_backend():
    """Test getting a backend from the runtime service."""
    with patch("qbraid.runtime.qiskit.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = FakeService()
        assert isinstance(
            mock_runtime_service().backend("generic_backend_5q", instance=None), GenericBackendV2
        )


def test_build_runtime_profile():
    """Test building runtime profile for Qiskit backend."""
    with patch("qbraid.runtime.qiskit.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = FakeService()
        backend = FakeDevice(5)
        provider = QiskitRuntimeProvider(token="test_token", channel="test_channel")
        profile = provider._build_runtime_profile(backend)
        assert profile._data["device_id"] == "generic_backend_5q"
        assert profile._data["device_type"] == DeviceType.LOCAL_SIMULATOR.name
        assert profile._data["num_qubits"] == 5
        assert profile._data["max_shots"] == 8192

        qiskit_backend = QiskitBackend(profile, mock_runtime_service())
        assert isinstance(qiskit_backend, QiskitBackend)
        assert qiskit_backend.profile == profile


@pytest.mark.parametrize("device", fake_ibm_devices())
def test_retrieving_ibm_job(device):
    """Test retrieving a previously submitted IBM job."""
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=RuntimeWarning)
        qbraid_job = device.run(circuit, shots=1)

    ibm_job = qbraid_job._job
    assert isinstance(ibm_job, Job)


@pytest.mark.parametrize("device", fake_ibm_devices())
def test_cancel_completed_batch_error(device, run_inputs):
    """Test that cancelling a batch job that has already reached its
    final state raises an error."""
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=RuntimeWarning)
        job = device.run(run_inputs, shots=10)

    timeout = 30
    check_every = 2
    elapsed_time = 0

    while elapsed_time < timeout:
        if job.is_terminal_state():
            break

        time.sleep(check_every)
        elapsed_time += check_every

    if elapsed_time >= timeout:
        try:
            job.cancel()
        except JobStateError:
            pass

    with pytest.raises(JobStateError):
        job.cancel()


@patch("qbraid.runtime.qiskit.job.QiskitJob._get_job")
def test_init_without_provided_job(mock_get_job):
    """Test initializing a QiskitJob without providing a job."""
    job_id = "12345"
    mock_job = MagicMock()
    mock_get_job.return_value = mock_job
    job = QiskitJob(job_id)
    mock_get_job.assert_called_once()
    assert job._job == mock_job


def test_get_job_error_handling():
    """Test error handling when getting a job."""
    with pytest.raises(QbraidRuntimeError) as exc_info:
        _ = QiskitJob("12345")
    assert "Error retrieving job" in str(exc_info.value)


@pytest.fixture
def mock_qiskit_result():
    """Return a mock Qiskit result."""
    mock_result = Mock()
    mock_result.results = [Mock(), Mock()]
    meas1 = ["01"] * 9 + ["10"] + ["11"] * 4 + ["00"] * 6
    meas2 = ["0"] * 8 + ["1"] * 12
    mock_result.get_memory.side_effect = [meas1, meas2]
    mock_result.get_counts.side_effect = [{"01": 9, "10": 1, "11": 4, "00": 6}, {"0": 8, "1": 12}]
    return mock_result


def test_format_measurements():
    """Test formatting measurements into integers."""
    qr = QiskitResult()
    memory_list = ["010", "111"]
    expected = [[0, 1, 0], [1, 1, 1]]
    assert qr._format_measurements(memory_list) == expected


def test_measurements_single_circuit(mock_qiskit_result):
    """Test getting measurements from a single circuit."""
    qr = QiskitResult()
    qr._result = mock_qiskit_result
    mock_qiskit_result.results = [Mock()]
    expected = np.array([[0, 1]] * 9 + [[1, 0]] + [[1, 1]] * 4 + [[0, 0]] * 6)
    assert np.array_equal(qr.measurements(), expected)


def test_measurements_multiple_circuits(mock_qiskit_result):
    """Test getting measurements from multiple circuits."""
    qr = QiskitResult()
    qr._result = mock_qiskit_result
    expected_meas1 = np.array([[0, 1]] * 9 + [[1, 0]] + [[1, 1]] * 4 + [[0, 0]] * 6)
    expected_meas2 = np.array([[0, 0]] * 8 + [[0, 1]] * 12)
    expected = np.array([expected_meas1, expected_meas2])
    assert np.array_equal(qr.measurements(), expected)


def test_raw_counts(mock_qiskit_result):
    """Test getting raw counts from a Qiskit result."""
    qr = QiskitResult()
    qr._result = mock_qiskit_result
    expected = {"01": 9, "10": 1, "11": 4, "00": 6}
    assert qr.raw_counts() == expected

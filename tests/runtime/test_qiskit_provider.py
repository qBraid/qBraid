# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for QiskitProvider class

"""
import random
import time
from typing import Union
from unittest.mock import Mock, patch

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.providers.basic_provider.basic_provider_job import BasicProviderJob
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.providers.models import QasmBackendConfiguration
from qiskit_aer import AerJob
from qiskit_ibm_runtime import QiskitRuntimeService, RuntimeJob
from qiskit_ibm_runtime.qiskit_runtime_service import QiskitBackendNotFoundError

from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
from qbraid.runtime import DeviceType, JobStateError, TargetProfile
from qbraid.runtime.qiskit import QiskitBackend, QiskitJob, QiskitRuntimeProvider


def braket_circuit():
    """Returns low-depth, one-qubit Braket circuit to be used for testing."""
    import braket.circuits  # pylint: disable=import-outside-toplevel

    circuit = braket.circuits.Circuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
    return circuit


def cirq_circuit(meas=True):
    """Returns Low-depth, one-qubit Cirq circuit to be used for testing.
    If ``meas=True``, applies measurement operation to end of circuit."""
    import cirq  # pylint: disable=import-outside-toplevel

    q0 = cirq.GridQubit(0, 0)

    def basic_circuit():
        yield cirq.H(q0)
        yield cirq.Ry(rads=np.pi / 2)(q0)
        if meas:
            yield cirq.measure(q0, key="q0")

    circuit = cirq.Circuit()
    circuit.append(basic_circuit())
    return circuit


def qiskit_circuit(meas=True):
    """Returns Low-depth, one-qubit Qiskit circuit to be used for testing.
    If ``meas=True``, applies measurement operation to end of circuit."""
    import qiskit  # pylint: disable=import-outside-toplevel

    circuit = qiskit.QuantumCircuit(1, 1) if meas else qiskit.QuantumCircuit(1)
    circuit.h(0)
    circuit.ry(np.pi / 2, 0)
    if meas:
        circuit.measure(0, 0)
    return circuit


def run_inputs():
    """Returns list of test circuits for each available native provider."""
    circuits = []
    if "cirq" in NATIVE_REGISTRY:
        circuits.append(cirq_circuit(meas=False))
    if "qiskit" in NATIVE_REGISTRY:
        circuits.append(qiskit_circuit(meas=False))
    if "braket" in NATIVE_REGISTRY:
        circuits.append(braket_circuit())
    return circuits


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
        TargetProfile(backend.name, DeviceType.LOCAL_SIMULATOR, backend.num_qubits, program_spec)
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
@pytest.mark.parametrize("circuit", run_inputs())
def test_run_fake_qiskit_device_wrapper(qbraid_device, circuit):
    """Test run method from wrapped fake Qiskit backends"""
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, Union[BasicProviderJob, AerJob])


@pytest.mark.parametrize("qbraid_device", fake_ibm_devices())
def test_run_fake_batch_qiskit_device_wrapper(qbraid_device):
    """Test run method from wrapped fake Qiskit backends"""
    qbraid_job = qbraid_device.run(run_inputs(), shots=10)
    vendor_job = qbraid_job._job
    assert isinstance(qbraid_job, QiskitJob)
    assert isinstance(vendor_job, Union[BasicProviderJob, AerJob])


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
        assert profile._data["device_type"] == "LOCAL_SIMULATOR"
        assert profile._data["num_qubits"] == 5
        assert profile._data["max_shots"] == 8192
        # basically testing get_device too
        qiskit_backend = QiskitBackend(profile, mock_runtime_service())
        assert isinstance(qiskit_backend, QiskitBackend)
        assert qiskit_backend.profile == profile


@pytest.mark.parametrize("device", fake_ibm_devices())
def test_retrieving_ibm_job(device):
    """Test retrieving a previously submitted IBM job."""
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    qbraid_job = device.run(circuit, shots=1)
    ibm_job = qbraid_job._job
    assert isinstance(ibm_job, Union[RuntimeJob, AerJob])


@pytest.mark.parametrize("device", fake_ibm_devices())
def test_cancel_completed_batch_error(device):
    """Test that cancelling a batch job that has already reached its
    final state raises an error."""
    job = device.run(run_inputs(), shots=10)

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

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
Unit tests for OQCProvider class

"""
from unittest.mock import Mock, patch

import numpy as np
import pytest

from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
from qbraid.runtime import DeviceType, TargetProfile
from qbraid.runtime.oqc import OQCDevice, OQCJob, OQCProvider
from qbraid.transpiler import ConversionScheme

try:
    from qcaas_client.client import OQCClient, QPUTask

    oqc_not_installed = False
except ImportError:
    oqc_not_installed = True

pytest.mark.skipif(oqc_not_installed, reason="qcaas_client not installed")


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


def test_circuits():
    """Returns list of test circuits for each available native provider."""
    circuits = []
    if "cirq" in NATIVE_REGISTRY:
        circuits.append(cirq_circuit(meas=False))
    if "qiskit" in NATIVE_REGISTRY:
        circuits.append(qiskit_circuit(meas=False))
    if "braket" in NATIVE_REGISTRY:
        circuits.append(braket_circuit())
    return circuits


DEVICE_ID = "qpu:uk:2:d865b5a184"


def test_oqc_provider_device():
    """Test OQC provider and device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [{"id": DEVICE_ID, "num_qubits": 8}]
        provider = OQCProvider(api_key="fake_api_key")
        assert isinstance(provider, OQCProvider)
        assert isinstance(provider.client, OQCClient)
        assert provider.client == mock_client.return_value
        test_device = provider.get_device(DEVICE_ID)
        assert isinstance(test_device, OQCDevice)
        assert test_device.profile["device_id"] == DEVICE_ID


def test_build_runtime_profile():
    """Test building a runtime profile for OQC device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        provider = OQCProvider(api_key="fake_api_key")
        profile = provider._build_profile({"id": DEVICE_ID, "num_qubits": 8})
        assert isinstance(profile, TargetProfile)
        assert profile._data["device_id"] == DEVICE_ID
        assert profile._data["device_type"] == DeviceType.SIMULATOR
        assert profile._data["num_qubits"] == 8
        assert profile._data["program_spec"] == ProgramSpec(str, alias="qasm2")


class TestOQCClient:
    """Test class for OQC client."""

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def schedule_tasks(self, task: QPUTask, qpu_id):
        """Schedule tasks for the QPU."""
        qpu_id = qpu_id[::]
        return task


class TestOQCDevice(OQCDevice):
    """Test class for OQC device."""

    def __init__(
        self, id, oqc_client=None
    ):  # pylint: disable=redefined-builtin, super-init-not-called
        self._client = oqc_client or TestOQCClient("fake_api_key")
        self._profile = TargetProfile(
            device_id=id,
            device_type=DeviceType.SIMULATOR,
            num_qubits=8,
            program_spec=ProgramSpec(str, alias="qasm2"),
        )
        self._target_spec = ProgramSpec(str, alias="qasm2")
        self._scheme = ConversionScheme()


@pytest.mark.parametrize("circuit", test_circuits())
def test_run_fake_job(circuit):
    """Test running a fake job."""
    device = TestOQCDevice(DEVICE_ID)
    job = device.run(circuit)
    assert isinstance(job, OQCJob)


def test_run_batch_fake_job():
    """Test running a batch of fake jobs."""
    device = TestOQCDevice(DEVICE_ID)
    circuits = test_circuits()
    job = device.run(circuits)
    assert isinstance(job, list)
    assert len(job) == len(circuits)
    assert all(isinstance(j, OQCJob) for j in job)

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
Unit tests for QbraidDevice, QbraidJob, and QbraidJobResult classes using the qbraid_qir_simulator

"""
import random
from typing import Any, Optional

import cirq
import numpy as np
import pytest
from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.native import (
    ExperimentResult,
    QbraidDevice,
    QbraidJob,
    QbraidJobResult,
    QbraidProvider,
)
from qbraid.runtime.profile import TargetProfile
from qbraid.transpiler import Conversion, ConversionGraph, ConversionScheme

DEVICE_DATA = {
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

JOB_DATA = {
    "qbraidJobId": "qbraid_qir_simulator-jovyan-qjob-1234567890",
    "queuePosition": None,
    "queueDepth": None,
    "timeStamps": {"executionDuration": 16},
    "shots": 10,
    "circuitNumQubits": 5,
    "measurementCounts": {"11111": 4, "00000": 6},
    "qbraidDeviceId": "qbraid_qir_simulator",
    "vendorJobId": "afff09f1-d9e0-4dcb-8274-b984678d35c3",
    "status": "COMPLETED",
    "qbraidStatus": "COMPLETED",
    "vendor": "qbraid",
    "provider": "qbraid",
    "createdAt": "2024-05-23T01:39:11.288Z",
}

JOB_RESULT = {
    "vendorJobId": "afff09f1-d9e0-4dcb-8274-b984678d35c3",
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
    "timeStamps": {"executionDuration": 16},
    "qbraidDeviceId": "qbraid_qir_simulator",
    "shots": 10,
    "circuitNumQubits": 5,
    "tags": "{}",
}


class MockClient:
    """Mock client for testing."""

    def get_device(self, qbraid_id: Optional[str] = None, **kwargs):
        """Returns the device with the given ID."""
        if qbraid_id == "qbraid_qir_simulator":
            return DEVICE_DATA
        raise QuantumServiceRequestError("No devices found matching given criteria")

    def create_job(self, data: dict[str, Any]) -> dict[str, Any]:
        """Creates a new quantum job with the given data."""
        return JOB_DATA

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Returns the quantum job with the given ID."""
        JOB_DATA["result"] = JOB_RESULT
        return JOB_DATA


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
def mock_profile():
    """Mock profile for testing."""
    return TargetProfile(
        device_id="mock",
        device_type="SIMULATOR",
        action_type="OPENQASM",
        num_qubits=42,
        program_spec=None,
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
def mock_basic_device(mock_profile):
    """Generic mock device for testing."""
    return MockDevice(profile=mock_profile)


def _is_uniform_comput_basis(array: np.ndarray) -> bool:
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


def _uniform_state_circuit(num_qubits: Optional[int] = None) -> cirq.Circuit:
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

    Returns:
        cirq.Circuit: The resulting circuit where the measurement outcome of all qubits is
                      either all |0⟩s or all |1⟩s.

    Raises:
        ValueError: If the number of qubits provided is less than 1.
    """
    if num_qubits is not None and num_qubits < 1:
        raise ValueError("Number of qubits must be at least 1.")

    num_qubits = num_qubits or random.randint(10, 20)

    # Create n qubits
    qubits = [cirq.LineQubit(i) for i in range(num_qubits)]

    # Create a circuit
    circuit = cirq.Circuit()

    # Add a Hadamard gate to the first qubit
    circuit.append(cirq.H(qubits[0]))

    # Entangle all other qubits with the first qubit
    for qubit in qubits[1:]:
        circuit.append(cirq.CNOT(qubits[0], qubit))

    # Measure all qubits
    circuit.append(cirq.measure(*qubits, key="result"))

    return circuit


@pytest.fixture
def cirq_uniform():
    """Cirq circuit used for testing."""
    return _uniform_state_circuit


def test_qir_simulator_workflow(mock_client, cirq_uniform):
    """Test qir simulator qbraid device job submission and result retrieval."""
    circuit = cirq_uniform(num_qubits=5)
    num_qubits = len(circuit.all_qubits())

    provider = QbraidProvider(client=mock_client)
    device = provider.get_device("qbraid_qir_simulator")

    shots = 10
    job = device.run(circuit, shots=shots)
    assert isinstance(job, QbraidJob)
    assert job.is_terminal_state()

    result = job.result()
    assert isinstance(result, QbraidJobResult)
    assert isinstance(result.result, ExperimentResult)
    assert repr(result).startswith("QbraidJobResult")
    assert result.success

    counts = result.measurement_counts()
    probabilities = result.measurement_probabilities()
    assert len(counts) == len(probabilities) == 2
    assert sum(probabilities.values()) == 1.0

    metadata = result.metadata()
    assert metadata["num_shots"] == shots
    assert metadata["num_qubits"] == num_qubits
    assert isinstance(metadata["execution_duration"], int)

    measurements = result.measurements()
    assert _is_uniform_comput_basis(measurements)


def test_update_scheme(mock_qbraid_device):
    """Test updating ConversionScheme."""
    graph = mock_qbraid_device.scheme.conversion_graph.copy()
    new_conversion = Conversion("charlie", "alice", lambda x: x)
    graph.add_conversion(new_conversion)

    assert graph != mock_qbraid_device.scheme.conversion_graph

    mock_qbraid_device.update_scheme(conversion_graph=graph)

    assert graph == mock_qbraid_device.scheme.conversion_graph


def test_queue_depth_raises(mock_basic_device):
    """Test raising exception when queue depth is unavailable."""
    with pytest.raises(ResourceNotFoundError):
        mock_basic_device.queue_depth()

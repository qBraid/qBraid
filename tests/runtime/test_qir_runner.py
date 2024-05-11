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
Unit tests for QbraidDevice, QbraidJob, and QbraidJobResult classes using the qbraid_qir_simulator

"""
import random
import shutil
from typing import Optional

import cirq
import numpy as np
import pytest

from qbraid.runtime.job import QbraidJob
from qbraid.runtime.provider import QbraidProvider
from qbraid.runtime.result import ExperimentResult, QbraidJobResult

# pylint: disable=redefined-outer-name

skip_runner_tests = shutil.which("qir-runner") is None
REASON = "qir-runner executable not available"


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
    yield _uniform_state_circuit


@pytest.mark.skipif(skip_runner_tests, reason=REASON)
def test_qir_simulator_workflow(cirq_uniform):
    """Test qir simulator qbraid device job submission and result retrieval."""
    circuit = cirq_uniform()
    num_qubits = len(circuit.all_qubits())

    provider = QbraidProvider()
    device = provider.get_device("qbraid_qir_simulator")

    shots = random.randint(500, 1000)
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

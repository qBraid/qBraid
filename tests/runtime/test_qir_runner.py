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
Unit tests for qir-runner Python simulator wrapper.

"""
import random
import shutil
from typing import Optional

import cirq
import numpy as np
import pytest
from qbraid_qir import dumps
from qbraid_qir.cirq import cirq_to_qir

from qbraid.runtime.sim import Result, Simulator

# pylint: disable=redefined-outer-name


skip_runner_tests = shutil.which("qir-runner") is None
REASON = "qir-runner executable not available"

stdout = """
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  1
OUTPUT  RESULT  1
END     0
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  1
OUTPUT  RESULT  1
END     0
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  1
OUTPUT  RESULT  1
END     0
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  0
OUTPUT  RESULT  0
END     0
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  1
OUTPUT  RESULT  1
END     0
"""


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


def _sparse_circuit(num_qubits: Optional[int] = None) -> cirq.Circuit:
    """
    Generates a quantum circuit designed to benchmark the performance of a sparse simulator.

    This circuit is structured to maintain a level of sparsity in the system's state vector, making
    it a good candidate for testing sparse quantum simulators. Sparse simulators excel in
    simulating circuits where the state vector remains sparse, i.e., most of its elements are zero
    or can be efficiently represented.

    Args:
        num_qubits (optional, int): The number of qubits to use in the circuit. If not provided,
                                    a random number of qubits between 10 and 20 will be used.

    Returns:
        cirq.Circuit: The constructed circuit for benchmarking
    """
    num_qubits = num_qubits or random.randint(10, 20)
    # Create a circuit
    circuit = cirq.Circuit()

    # Create qubits
    qubits = cirq.LineQubit.range(num_qubits)

    # Apply Hadamard gates to the first half of the qubits
    for qubit in qubits[: num_qubits // 2]:
        circuit.append(cirq.H(qubit))

    # Apply a CNOT ladder
    for i in range(num_qubits - 1):
        circuit.append(cirq.CNOT(qubits[i], qubits[i + 1]))

    # Apply Z gates to randomly selected qubits
    for qubit in random.sample(qubits, k=num_qubits // 2):
        circuit.append(cirq.Z(qubit))

    # Measurement (optional)
    circuit.append(cirq.measure(*qubits, key="result"))

    return circuit


@pytest.fixture
def cirq_sparse():
    """Cirq circuit used for testing."""
    yield _sparse_circuit


@pytest.mark.skipif(skip_runner_tests, reason=REASON)
def test_sparse_simulator(cirq_sparse):
    """Test qir-runner sparse simulator python wrapper(s)."""
    circuit = cirq_sparse()
    num_qubits = len(circuit.all_qubits())

    file_prefix = "sparse_simulator_test"
    module = cirq_to_qir(circuit, name=file_prefix)
    dumps(module)
    simulator = Simulator()

    shots = random.randint(500, 1000)
    result = simulator.run(f"{file_prefix}.bc", shots=shots)
    assert isinstance(result, Result)

    counts = result.measurement_counts()
    probabilities = result.measurement_probabilities()
    assert len(counts) == len(probabilities) == 2
    assert sum(probabilities.values()) == 1.0

    metadata = result.metadata()
    assert metadata["num_shots"] == shots
    assert metadata["num_qubits"] == num_qubits
    assert isinstance(metadata["execution_duration"], float)

    measurements = result.measurements
    assert _is_uniform_comput_basis(measurements)


def test_result():
    """Test the Result class."""
    result = Result(stdout, execution_duration=100)
    parsed_expected = {"q0": [1, 1, 1, 0, 1], "q1": [1, 1, 1, 0, 1]}
    measurements_expected = np.array([[1, 1], [1, 1], [1, 1], [0, 0], [1, 1]])
    counts_expected = {"00": 1, "11": 4}
    counts_decimal_expected = {0: 1, 3: 4}
    probabilities_expected = {"00": 0.2, "11": 0.8}
    metadata_expected = {
        "num_shots": 5,
        "num_qubits": 2,
        "execution_duration": 100,
        "measurements": measurements_expected,
        "measurement_counts": counts_expected,
        "measurement_probabilities": probabilities_expected,
    }
    assert result._parsed_data == parsed_expected
    assert np.array_equal(result.measurements, measurements_expected)
    assert result.measurement_counts() == counts_expected
    assert result.measurement_counts(decimal=True) == counts_decimal_expected
    assert result.measurement_probabilities() == probabilities_expected

    metadata_out = result.metadata()
    assert metadata_out["num_shots"] == metadata_expected["num_shots"]
    assert metadata_out["num_qubits"] == metadata_expected["num_qubits"]
    assert metadata_out["execution_duration"] == metadata_expected["execution_duration"]
    assert repr(result).startswith("Result")

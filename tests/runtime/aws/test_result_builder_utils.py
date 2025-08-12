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
Unit tests for result builder utility functions for partial measurements

"""
from qbraid.runtime.aws.result_builder import marginal_count, marginal_measurement


def test_marginal_measurement_basic():
    """Test basic marginal measurement extraction."""
    measurements = [[0, 1, 0, 1], [1, 0, 1, 0], [0, 0, 1, 1]]
    qubit_indices = [0, 2]

    result = marginal_measurement(measurements, qubit_indices)
    expected = [[0, 0], [1, 1], [0, 1]]

    assert result == expected


def test_marginal_measurement_single_qubit():
    """Test marginal measurement with single qubit."""
    measurements = [[0, 1, 0], [1, 0, 1], [0, 1, 1]]
    qubit_indices = [1]

    result = marginal_measurement(measurements, qubit_indices)
    expected = [[1], [0], [1]]

    assert result == expected


def test_marginal_measurement_all_qubits():
    """Test marginal measurement with all qubits (should return original)."""
    measurements = [[0, 1, 0], [1, 0, 1]]
    qubit_indices = [0, 1, 2]

    result = marginal_measurement(measurements, qubit_indices)
    expected = [[0, 1, 0], [1, 0, 1]]

    assert result == expected


def test_marginal_measurement_reverse_order():
    """Test marginal measurement with indices in reverse order."""
    measurements = [[0, 1, 0, 1], [1, 0, 1, 0]]
    qubit_indices = [3, 1, 0]

    result = marginal_measurement(measurements, qubit_indices)
    expected = [[1, 1, 0], [0, 0, 1]]

    assert result == expected


def test_marginal_measurement_empty_measurements():
    """Test marginal measurement with empty measurements list."""
    measurements = []
    qubit_indices = [0, 1]

    result = marginal_measurement(measurements, qubit_indices)
    expected = []

    assert result == expected


def test_marginal_measurement_empty_indices():
    """Test marginal measurement with empty qubit indices."""
    measurements = [[0, 1, 0], [1, 0, 1]]
    qubit_indices = []

    result = marginal_measurement(measurements, qubit_indices)
    expected = [[], []]

    assert result == expected


def test_marginal_count_basic():
    """Test basic marginal count computation."""
    count_dict = {"0101": 10, "1010": 5, "0110": 3}
    qubit_indices = [0, 2]

    result = marginal_count(count_dict, qubit_indices)
    expected = {"00": 10, "11": 5, "01": 3}

    assert result == expected


def test_marginal_count_with_aggregation():
    """Test marginal count with aggregation of similar patterns."""
    count_dict = {"0101": 10, "0111": 5, "1101": 3, "1111": 2}
    qubit_indices = [0, 2]

    result = marginal_count(count_dict, qubit_indices)
    expected = {"00": 10, "01": 5, "10": 3, "11": 2}

    assert result == expected


def test_marginal_count_aggregation_same_pattern():
    """Test marginal count where different bitstrings map to same pattern."""
    count_dict = {"0101": 10, "0001": 5, "0111": 3, "0011": 2}
    qubit_indices = [0, 3]  # First and last bits

    result = marginal_count(count_dict, qubit_indices)
    # "0101" -> "01", "0001" -> "01", "0111" -> "01", "0011" -> "01"
    expected = {"01": 20}  # 10 + 5 + 3 + 2

    assert result == expected


def test_marginal_count_single_qubit():
    """Test marginal count with single qubit."""
    count_dict = {"010": 10, "110": 5, "001": 3}
    qubit_indices = [1]

    result = marginal_count(count_dict, qubit_indices)
    expected = {"1": 15, "0": 3}  # "010"->1, "110"->1, "001"->0

    assert result == expected


def test_marginal_count_all_qubits():
    """Test marginal count with all qubits (should return original)."""
    count_dict = {"010": 10, "110": 5, "001": 3}
    qubit_indices = [0, 1, 2]

    result = marginal_count(count_dict, qubit_indices)
    expected = {"010": 10, "110": 5, "001": 3}

    assert result == expected


def test_marginal_count_empty_dict():
    """Test marginal count with empty count dictionary."""
    count_dict = {}
    qubit_indices = [0, 1]

    result = marginal_count(count_dict, qubit_indices)
    expected = {}

    assert result == expected


def test_marginal_count_empty_indices():
    """Test marginal count with empty qubit indices."""
    count_dict = {"010": 10, "110": 5}
    qubit_indices = []

    result = marginal_count(count_dict, qubit_indices)
    expected = {"": 15}  # All counts aggregated to empty string

    assert result == expected


def test_marginal_count_complex_aggregation():
    """Test complex marginal count with multiple aggregations."""
    count_dict = {
        "0000": 10,
        "0001": 5,
        "0010": 3,
        "0011": 2,
        "1000": 8,
        "1001": 4,
        "1010": 6,
        "1011": 1,
    }
    qubit_indices = [0, 2]  # First and third bits

    result = marginal_count(count_dict, qubit_indices)
    # Let me recalculate:
    # "0000" -> bits [0,2] -> "00" (10)
    # "0001" -> bits [0,2] -> "00" (5)
    # "0010" -> bits [0,2] -> "01" (3)
    # "0011" -> bits [0,2] -> "01" (2)
    # "1000" -> bits [0,2] -> "10" (8)
    # "1001" -> bits [0,2] -> "10" (4)
    # "1010" -> bits [0,2] -> "11" (6)
    # "1011" -> bits [0,2] -> "11" (1)
    expected = {"00": 15, "01": 5, "10": 12, "11": 7}  # 10 + 5  # 3 + 2  # 8 + 4  # 6 + 1

    assert result == expected


def test_marginal_count_reverse_order_indices():
    """Test marginal count with indices in reverse order."""
    count_dict = {"0101": 10, "1010": 5}
    qubit_indices = [3, 1, 0]  # Reverse order

    result = marginal_count(count_dict, qubit_indices)
    expected = {"110": 10, "001": 5}  # "0101"->bits[3,1,0]->"110", "1010"->bits[3,1,0]->"001"

    assert result == expected

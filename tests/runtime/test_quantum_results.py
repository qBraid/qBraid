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
Unit tests for retrieving and post-processing experimental results.

"""
import os

import pytest

from qbraid.runtime.result import GateModelJobResult, normalize_measurement_counts

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM/AWS storage)"


@pytest.mark.parametrize(
    "counts_raw, expected_out, include_zero_values",
    [
        ({" 1": 0, "0": 550}, {"0": 550}, False),
        ({"10": 479, "1 1": 13, "0 0 ": 496}, {"00": 496, "10": 479, "11": 13}, False),
        ({" 1": 474, "0": 550}, {"0": 550, "1": 474}, True),
        ({"10": 479, "1 1": 13, "0 0 ": 496}, {"00": 496, "01": 0, "10": 479, "11": 13}, True),
        (
            {"10 1": 586, "11  0  ": 139, "0 01": 496, "  010": 543, "11 1": 594},
            {
                "000": 0,
                "001": 496,
                "010": 543,
                "011": 0,
                "100": 0,
                "101": 586,
                "110": 139,
                "111": 594,
            },
            True,
        ),
    ],
)
def test_format_counts(counts_raw, expected_out, include_zero_values):
    """Test formatting of raw measurement counts."""
    counts_out = GateModelJobResult.format_counts(
        counts_raw, include_zero_values=include_zero_values
    )
    assert counts_out == expected_out  # check equivalance
    assert list(counts_out.items()) == list(expected_out.items())  # check ordering of keys


def test_normalize_different_key_lengths():
    """Test normalization of measurement counts with different key lengths."""
    measurements = [{"0": 10, "1": 15}, {"00": 5, "01": 8, "10": 12}]
    expected = [{"00": 10, "01": 15}, {"00": 5, "01": 8, "10": 12}]
    assert normalize_measurement_counts(measurements) == expected


def test_normalize_same_key_lengths():
    """Test normalization of measurement counts with the same key lengths."""
    measurements = [{"00": 7, "01": 9}, {"10": 4, "11": 3}]
    expected = [{"00": 7, "01": 9}, {"10": 4, "11": 3}]
    assert normalize_measurement_counts(measurements) == expected


def test_empty_input():
    """Test normalization of empty input."""
    measurements = []
    expected = []
    assert normalize_measurement_counts(measurements) == expected


def test_empty_dicts():
    """Test normalization of empty dicts."""
    measurements = [{}, {}, {"00": 1, "11": 2}]
    expected = [{}, {}, {"00": 1, "11": 2}]
    assert normalize_measurement_counts(measurements) == expected


def test_normalize_single_dict():
    """Test normalization of a single dict."""
    measurements = [{"0": 2, "1": 3, "10": 4, "11": 1}]
    expected = [{"00": 2, "01": 3, "10": 4, "11": 1}]
    assert normalize_measurement_counts(measurements) == expected

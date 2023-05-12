# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for post-processing of measurement results.

"""
import pytest

from qbraid.devices.result import _format_counts


@pytest.mark.parametrize(
    "counts_raw, expected_out",
    [
        ({" 1": 474, "0": 550}, {"0": 550, "1": 474}),
        ({"10": 479, "1 1": 13, "0 0 ": 496}, {"00": 496, "01": 0, "10": 479, "11": 13}),
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
        ),
    ],
)
def test_format_counts(counts_raw, expected_out):
    counts_out = _format_counts(counts_raw)
    assert counts_out == expected_out  # check equivalance
    assert list(counts_out.items()) == list(expected_out.items())  # check ordering of keys

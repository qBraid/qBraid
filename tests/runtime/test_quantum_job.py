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
Unit tests for quantum jobs functions and data types

"""
import pytest

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.native.job import QbraidJob

status_data = [
    (JobStatus.INITIALIZING, False),
    (JobStatus.QUEUED, False),
    (JobStatus.RUNNING, False),
    (JobStatus.CANCELLING, False),
    (JobStatus.CANCELLED, True),
    (JobStatus.COMPLETED, True),
    (JobStatus.FAILED, True),
    (JobStatus.UNKNOWN, False),
]


@pytest.mark.parametrize("status_tuple", status_data)
def test_status_from_raw(status_tuple):
    """Test converting str status representation to JobStatus object."""
    status_obj, _ = status_tuple
    status_str = status_obj.name
    status_obj_test = QbraidJob._map_status(status_str)
    assert status_obj == status_obj_test


@pytest.mark.parametrize("status", ["INITIIZING", "QUDEUED", "CANCELLLED"])
def test_status_from_raw_error(status):
    """Test raising exception while converting invalid str status representation."""
    with pytest.raises(ValueError):
        QbraidJob._map_status(status)


@pytest.mark.parametrize(
    "status_tuple",
    [
        ("QUEUED", JobStatus.QUEUED),
        ("VALIDATING", JobStatus.VALIDATING),
        (None, JobStatus.UNKNOWN),
    ],
)
def test_map_status(status_tuple):
    """Test setting initial job status."""
    status_input, status_expected = status_tuple
    assert QbraidJob._map_status(status_input) == status_expected


def test_map_status_raises():
    """Test raising exception for bad status type."""
    with pytest.raises(ValueError):
        QbraidJob._map_status(0)

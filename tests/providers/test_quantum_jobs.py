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
Unit tests for quantum jobs functions and data types

"""
import pytest

from qbraid import job_wrapper
from qbraid.exceptions import QbraidError
from qbraid.providers.enums import JobStatus
from qbraid.providers.job import QuantumJob

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
def test_is_status_final(status_tuple):
    """Test identifying job status objects that are in final state"""
    status_obj, final_expected = status_tuple
    status_str = status_obj.name
    final_obj = QuantumJob.status_final(status_obj)
    final_str = QuantumJob.status_final(status_str)
    assert final_obj == final_expected
    assert final_str == final_expected


@pytest.mark.parametrize("status", [0, {}, []])
def test_is_status_final_error(status):
    """Test raiseing exception while checking if job status is final"""
    with pytest.raises(TypeError):
        QuantumJob.status_final(status)


@pytest.mark.parametrize("status_tuple", status_data)
def test_status_from_raw(status_tuple):
    """Test converting str status representation to JobStatus object."""
    status_obj, _ = status_tuple
    status_str = status_obj.name
    status_obj_test = QuantumJob._map_status(status_str)
    assert status_obj == status_obj_test


@pytest.mark.parametrize("status", ["INITIIZING", "QUDEUED", "CANCELLLED"])
def test_status_from_raw_error(status):
    """Test raising exception while converting invalid str status representation."""
    with pytest.raises(ValueError):
        QuantumJob._map_status(status)


@pytest.mark.parametrize(
    "status_tuple",
    [
        (JobStatus.QUEUED, JobStatus.QUEUED),
        ("VALIDATING", JobStatus.VALIDATING),
        (None, JobStatus.UNKNOWN),
    ],
)
def test_map_status(status_tuple):
    """Test setting initial job status."""
    status_input, status_expected = status_tuple
    assert QuantumJob._map_status(status_input) == status_expected


def test_map_status_raises():
    """Test raising exception for bad status type."""
    with pytest.raises(ValueError):
        QuantumJob._map_status(0)


def test_job_wrapper_id_error():
    """Test raising job wrapper error due to invalid job ID."""
    with pytest.raises(QbraidError):
        job_wrapper("Id123")

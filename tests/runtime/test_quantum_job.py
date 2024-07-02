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
from qbraid.runtime.exceptions import DeviceProgramTypeMismatchError, ResourceNotFoundError
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


def get_expected_message(program, expected_type, action_type):
    """Generate the expected error message dynamically."""
    if program is None:
        program_type = "NoneType"
    else:
        program_type = type(program).__name__
    return (
        f"Incompatible program type: '{program_type}'. "
        f"Device action type '{action_type}' requires a program of type '{expected_type}'."
    )


class MockProgram:
    """Mock class for testing DeviceProgramTypeMismatchError."""


@pytest.mark.parametrize(
    "program, expected_type, action_type",
    [
        (MockProgram(), "QuantumProgram", "Compute"),
        (object(), "QuantumProgram", "Compute"),
        (MockProgram(), "MockProgram", "Compute"),
        (None, "QuantumProgram", "Compute"),
    ],
)
def test_device_program_type_mismatch_error(program, expected_type, action_type):
    """Test DeviceProgramTypeMismatchError with various scenarios."""
    expected_message = get_expected_message(program, expected_type, action_type)
    with pytest.raises(DeviceProgramTypeMismatchError) as exc_info:
        raise DeviceProgramTypeMismatchError(program, expected_type, action_type)

    assert str(exc_info.value) == expected_message


class FakeDevice:
    """Fake device class for testing."""

    def __init__(self, name, client):
        self.name = name
        self.client = client


def test_qbraid_job_device():
    """Test setting and getting device."""
    job = QbraidJob("test_job")
    with pytest.raises(ResourceNotFoundError):
        job.device  # pylint: disable=pointless-statement

    fake_device = FakeDevice("test_device", "test_client")

    job2 = QbraidJob("test_job", device=fake_device)
    assert job2.device == fake_device
    assert job2.client == "test_client"

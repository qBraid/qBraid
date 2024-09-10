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
# pylint: disable=redefined-outer-name
from unittest.mock import patch

import pytest

from qbraid.runtime import QuantumJob
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import (
    DeviceProgramTypeMismatchError,
    JobStateError,
    ResourceNotFoundError,
)
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


class FakeQbraidJob(QbraidJob):
    """Fake QbraidJob class for testing."""

    def __init__(self, job_id, terminal, device=None, client=None):
        super().__init__(job_id, device)
        self._terminal = terminal
        self._client = client

    def is_terminal_state(self):
        """Check if the job is in a terminal state."""
        return self._terminal


class FakeQbraidClient:
    """Fake QbraidClient class for testing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def cancel_job(self, qbraid_id=None, object_id=None):  # pylint: disable=unused-argument
        """Cancel a job."""
        return None


def test_cancel_job():
    """Test cancelling a job."""
    terminal_job = FakeQbraidJob("test_job", True)
    with pytest.raises(JobStateError):
        terminal_job.cancel()

    nonterminal_job = FakeQbraidJob("test_job", False, client=FakeQbraidClient())
    assert nonterminal_job.cancel() is None


class MockQuantumJob(QuantumJob):
    """Mock class for testing QuantumJob functions."""

    def __init__(self, job_id, device=None, **kwargs):
        super().__init__(job_id, device, **kwargs)
        self._status = "PENDING"

    def status(self):
        return self._status

    def cancel(self):
        pass

    def result(self):
        pass


@pytest.fixture
def quantum_job():
    """Return a mock QuantumJob object"""
    job = MockQuantumJob(job_id="test_job_id")
    return job


def test_wait_for_final_state_success(quantum_job):
    """Mocking the status to change to a final state after some time"""
    with patch.object(quantum_job, "is_terminal_state", side_effect=[False, False, True]):
        quantum_job.wait_for_final_state(timeout=1, poll_interval=0.1)


def test_wait_for_final_state_timeout(quantum_job):
    """Mocking the status to never change to a final state"""
    with patch.object(quantum_job, "is_terminal_state", return_value=False):
        with pytest.raises(JobStateError):
            quantum_job.wait_for_final_state(timeout=0.2, poll_interval=0.1)


def test_invalid_job_status_value():
    """Test that an invalid status value raises a ValueError."""
    with pytest.raises(ValueError, match="Invalid status value: INVALID_STATUS"):
        JobStatus._get_default_message("INVALID_STATUS")


def test_set_job_status_message():
    """Test that a custom status message can be set."""
    status = JobStatus.QUEUED
    assert status.default_message == "job is queued"
    assert status.status_message is None

    status.set_status_message("Job is in custom state")
    assert status.status_message == "Job is in custom state"
    assert repr(status) == "<QUEUED: 'Job is in custom state'>"

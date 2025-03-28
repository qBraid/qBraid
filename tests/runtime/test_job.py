# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for quantum jobs functions and data types

"""
from unittest.mock import patch

import pytest

from qbraid.programs import ExperimentType
from qbraid.runtime import QuantumJob
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import (
    DeviceProgramTypeMismatchError,
    JobStateError,
    QbraidRuntimeError,
    ResourceNotFoundError,
)
from qbraid.runtime.native.job import QbraidJob

from ._resources import JOB_DATA_QIR


def get_expected_message(program, expected_type, experiment_type):
    """Generate the expected error message dynamically."""
    if program is None:
        program_type = "NoneType"
    else:
        program_type = type(program).__name__
    return (
        f"Incompatible program type: '{program_type}'. "
        f"Experiment type '{experiment_type}' requires a program of type '{expected_type}'."
    )


class MockProgram:
    """Mock class for testing DeviceProgramTypeMismatchError."""


@pytest.mark.parametrize(
    "program, expected_type, experiment_type",
    [
        (MockProgram(), "QuantumProgram", "Compute"),
        (object(), "QuantumProgram", "Compute"),
        (MockProgram(), "MockProgram", "Compute"),
        (None, "QuantumProgram", "Compute"),
    ],
)
def test_device_program_type_mismatch_error(program, expected_type, experiment_type):
    """Test DeviceProgramTypeMismatchError with various scenarios."""
    expected_message = get_expected_message(program, expected_type, experiment_type)
    with pytest.raises(DeviceProgramTypeMismatchError) as excinfo:
        raise DeviceProgramTypeMismatchError(program, expected_type, experiment_type)

    assert str(excinfo.value) == expected_message


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

    def __init__(
        self,
        *args,
        init_status="FAILED",
        init_status_text="Some error message",
        fail_cancel=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._job_data = JOB_DATA_QIR.copy()
        self._job_data["status"] = init_status
        self._job_data["statusText"] = init_status_text
        self._fail_cancel = fail_cancel

    def get_job(self, job_id):  # pylint: disable=unused-argument
        """Get the job data."""
        status_data_copy = self._job_data.copy()
        if self._job_data["status"] == "CANCELLING":
            self._job_data["statusText"] = ""
            self._job_data["status"] = "CANCELLED"
        return status_data_copy

    def cancel_job(self, qbraid_id):  # pylint: disable=unused-argument
        """Cancel a job."""
        if self._fail_cancel:
            self._job_data["status"] = "COMPLETED"
            self._job_data["statusText"] = ""
        else:
            self._job_data["status"] = "CANCELLING"
            self._job_data["statusText"] = ""


@pytest.fixture
def mock_client():
    """Return a mock QbraidClient object."""
    return FakeQbraidClient()


@pytest.fixture
def mock_device(mock_client):
    """Return a mock QbraidDevice object."""
    return FakeDevice("test_device", client=mock_client)


@pytest.fixture
def mock_job(mock_device, mock_client):
    """Return a mock QbraidJob object."""
    return QbraidJob("test_job", device=mock_device, client=mock_client)


def test_cancel_job():
    """Test cancelling a job."""
    terminal_job = FakeQbraidJob("test_job", True)
    with pytest.raises(JobStateError):
        terminal_job.cancel()

    nonterminal_job = FakeQbraidJob(
        "test_job", False, client=FakeQbraidClient(init_status="RUNNING", init_status_text="")
    )
    assert nonterminal_job.cancel() is None

    nonterminal_job = FakeQbraidJob(
        "test_job",
        False,
        client=FakeQbraidClient(init_status="RUNNING", init_status_text="", fail_cancel=True),
    )
    with pytest.raises(QbraidRuntimeError):
        nonterminal_job.cancel()


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


@pytest.mark.asyncio
async def test_async_wait_for_final_state_success(quantum_job):
    """Ensures the async method completes when the job reaches a terminal state."""
    with patch.object(quantum_job, "is_terminal_state", side_effect=[False, False, True]):
        await quantum_job._wait_for_final_state(timeout=1, poll_interval=0.1)


@pytest.mark.asyncio
async def test_async_wait_for_final_state_timeout(quantum_job):
    """Ensures the async method raises TimeoutError if the job never completes."""
    with patch.object(quantum_job, "is_terminal_state", return_value=False):
        with pytest.raises(TimeoutError):
            await quantum_job._wait_for_final_state(timeout=0.2, poll_interval=0.1)


@pytest.mark.asyncio
async def test_async_result_success(quantum_job):
    """Test that async_result returns the job result after reaching terminal state."""
    mock_result = "expected_result"

    with patch.object(quantum_job, "is_terminal_state", side_effect=[False, True]):
        with patch.object(quantum_job, "result", return_value=mock_result):
            result = await quantum_job.async_result(timeout=1, poll_interval=0.1)
            assert result == mock_result


@pytest.mark.asyncio
async def test_async_result_timeout(quantum_job):
    """Test that async_result raises TimeoutError if job never reaches terminal state."""
    with patch.object(quantum_job, "is_terminal_state", return_value=False):
        with pytest.raises(TimeoutError):
            await quantum_job.async_result(timeout=0.2, poll_interval=0.1)


def test_wait_for_final_state_success(quantum_job):
    """Mocking the status to change to a final state after some time"""
    with patch.object(quantum_job, "is_terminal_state", side_effect=[False, False, True]):
        quantum_job.wait_for_final_state(timeout=1, poll_interval=0.1)


def test_wait_for_final_state_timeout(quantum_job):
    """Mocking the status to never change to a final state"""
    with patch.object(quantum_job, "is_terminal_state", return_value=False):
        with pytest.raises(TimeoutError):
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

    custom_status_message = "Custom status message"
    status.set_status_message(custom_status_message)
    assert status.status_message == custom_status_message
    assert repr(status) == f"<QUEUED: '{custom_status_message}'>"


def test_set_job_status_from_status_text(mock_job):
    """Test that a status message is set correctly from statusText job data recieved from client."""
    status = mock_job.status()
    assert status == JobStatus.FAILED
    assert status.status_message == "Some error message"


def test_job_status_enum_call_method():
    """Test that the JobStatus enum can be called as a function."""
    status = JobStatus.QUEUED
    new_status = status()
    assert new_status == status


def test_job_get_result_cls_raises_for_mismatch_expt_type():
    """Test that get_result_data_cls raises a ValueError for unsupported experiment type."""
    with pytest.raises(
        ValueError, match="Unsupported device_id 'aws_sv1' or experiment_type 'PHOTONIC'"
    ):
        QbraidJob.get_result_data_cls("aws_sv1", ExperimentType.PHOTONIC)

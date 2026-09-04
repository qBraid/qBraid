# Copyright 2026 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for the QPerfect (MIMIQ) job.

"""

from unittest.mock import patch

import pytest

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.qperfect import QPerfectJob, QPerfectJobError


def _job(connection, device=None) -> QPerfectJob:
    """Build a QPerfectJob wired to the mocked connection."""
    return QPerfectJob("exec-1", connection=connection, device=device)


@pytest.mark.parametrize(
    "mimiq_status, expected",
    [
        ("NEW", JobStatus.QUEUED),
        ("RUNNING", JobStatus.RUNNING),
        ("DONE", JobStatus.COMPLETED),
        ("ERROR", JobStatus.FAILED),
        ("CANCELED", JobStatus.CANCELLED),
    ],
)
def test_status_mapping(mock_connection, mimiq_status, expected):
    """Each MIMIQ status string maps to the right qBraid JobStatus."""
    mock_connection.connection.requestInfo.return_value.status = mimiq_status
    assert _job(mock_connection).status() == expected


def test_unknown_status_raises(mock_connection):
    """A status outside the known mapping surfaces instead of reading as UNKNOWN.

    MIMIQ adding an enum member should name itself in the error, not silently degrade a
    live job to an indeterminate state.
    """
    mock_connection.connection.requestInfo.return_value.status = "SOMETHING_ELSE"
    with pytest.raises(QPerfectJobError, match="unrecognized job status 'SOMETHING_ELSE'"):
        _job(mock_connection).status()


def test_missing_status_field_raises(mock_connection):
    """mimiqlink returns the literal "Unknown" when the payload omits ``status``.

    The error names that value rather than reading as a mapped-but-unknown state.
    """
    mock_connection.connection.requestInfo.return_value.status = "Unknown"
    with pytest.raises(QPerfectJobError, match="unrecognized job status 'Unknown'"):
        _job(mock_connection).status()


def test_status_is_a_single_api_call(mock_connection):
    """status() issues exactly one requestInfo call, not one per state branch."""
    mock_connection.connection.requestInfo.return_value.status = "RUNNING"
    _job(mock_connection).status()
    assert mock_connection.connection.requestInfo.call_count == 1


def test_cancel(mock_connection):
    """Cancelling stops the execution on the underlying connection."""
    _job(mock_connection).cancel()
    mock_connection.connection.stopExecution.assert_called_once_with("exec-1")


def test_cancel_failure_raises_job_error(mock_connection):
    """A failed cancellation surfaces as a QPerfectJobError (not a raw mimiqlink error)."""
    mock_connection.connection.stopExecution.side_effect = ConnectionError("already terminal")
    with pytest.raises(QPerfectJobError):
        _job(mock_connection).cancel()


def test_result_counts_and_endianness(mock_connection, fake_result, device):
    """Results parse the MIMIQ histogram to little-endian bitstring counts."""
    mock_connection.get_results.return_value = [fake_result]
    result = _job(mock_connection, device=device).result()
    # BitString([1, 0]).to01() == "10" -> reversed "01" (qubit 0 is the rightmost bit).
    assert result.data.get_counts() == {"01": 60, "00": 40}
    assert result.success is True
    assert result.job_id == "exec-1"


def test_result_incomplete_raises(mock_connection):
    """A job that did not complete raises rather than returning empty data."""
    mock_connection.connection.requestInfo.return_value.status = "ERROR"
    with pytest.raises(QPerfectJobError):
        _job(mock_connection).result()


def test_result_failure_includes_mimiq_error_message(mock_connection):
    """MIMIQ's own explanation reaches the caller; it usually names the fix."""
    info = mock_connection.connection.requestInfo.return_value
    info.status = "ERROR"
    info.get.side_effect = lambda key, default: (
        "SVS: Not enough memory to execute circuit 1." if key == "errorMessage" else default
    )
    with pytest.raises(QPerfectJobError, match=r"^Job exec-1 failed: SVS: Not enough memory"):
        _job(mock_connection).result()


def test_result_cancelled_names_the_state_once(mock_connection):
    """A cancelled job says so in one clause, with no redundant status= suffix."""
    mock_connection.connection.requestInfo.return_value.status = "CANCELED"
    with pytest.raises(QPerfectJobError, match=r"^Job exec-1 was cancelled\.$"):
        _job(mock_connection).result()


def test_result_propagates_unrecognized_status(mock_connection):
    """An unmapped status surfaces from the status() poll, not from the failure branch."""
    mock_connection.connection.requestInfo.return_value.status = "SOMETHING_ELSE"
    with pytest.raises(QPerfectJobError, match="unrecognized job status 'SOMETHING_ELSE'"):
        _job(mock_connection).result()


def test_unknown_job_id_raises_resource_not_found(mock_connection):
    """An unknown job id surfaces as a qBraid error, not a raw mimiqlink ConnectionError.

    MIMIQ answers a lookup for a nonexistent execution with a 500, so there is no 404 to
    distinguish; any lookup failure becomes ResourceNotFoundError.
    """
    mock_connection.connection.requestInfo.side_effect = ConnectionError(
        "Failed to retrieve execution details for exec-1. Server responded with 500"
    )
    with pytest.raises(ResourceNotFoundError, match="Could not retrieve execution details"):
        _job(mock_connection).status()


def test_default_connection_is_built_lazily(mock_connection):
    """Omitting the connection builds one via ``build_connection``."""
    with patch(
        "qbraid.runtime.qperfect.job.build_connection", return_value=mock_connection
    ) as built:
        job = QPerfectJob("exec-1")
    built.assert_called_once_with()
    assert job.connection is mock_connection


def test_result_normalizes_a_single_unlisted_result(mock_connection, fake_result, device):
    """A bare (non-list) ``get_results`` payload still parses to counts."""
    mock_connection.get_results.return_value = fake_result
    result = _job(mock_connection, device=device).result()
    assert result.data.get_counts() == {"01": 60, "00": 40}

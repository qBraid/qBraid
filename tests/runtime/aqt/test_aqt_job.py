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
Unit tests for the ``AQTJob`` sample-to-counts conversion, status mapping, cancellation, execution
time (derived from arnica ``timing_data``), and result rendering.

The ``mock_session`` / ``device`` fixtures come from ``conftest.py``; the arnica HTTP session is
mocked, so no network access occurs.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from qbraid.runtime.aqt import AQTJob, AQTJobError
from qbraid.runtime.aqt.job import _samples_to_counts
from qbraid.runtime.enums import JobStatus


def _result_payload(
    status: str,
    *,
    result: Any = None,
    message: str = "",
    workspace_id: str = "ws",
    resource_id: str = "res",
) -> dict[str, Any]:
    """Build a raw ``get_result`` dict that validates as an arnica ``ResultResponse``."""
    response: dict[str, Any] = {"status": status}
    if result is not None:
        response["result"] = result
    if status == "error":
        response["message"] = message
    if status == "ongoing":
        response["finished_count"] = 0
    return {
        "job": {
            "job_id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "resource_id": resource_id,
        },
        "response": response,
    }


# ---------------------------------------------------------------------------
# sample -> counts
# ---------------------------------------------------------------------------


def test_samples_to_counts_reverses_each_sample():
    """Each per-shot sample is reversed to qBraid little-endian: ``[[1, 0]] -> {"01": 1}``."""
    assert _samples_to_counts({0: [[1, 0]]}) == {"01": 1}


def test_samples_to_counts_single_circuit_aggregates():
    """Repeated samples within a single circuit aggregate into counts (reversed bitstrings)."""
    counts = _samples_to_counts({0: [[1, 0, 1], [1, 0, 1], [0, 0, 0]]})
    assert counts == {"101": 2, "000": 1}


def test_samples_to_counts_batch_returns_list_in_index_order():
    """A multi-circuit result returns a list of per-circuit counts ordered by circuit index."""
    counts = _samples_to_counts({0: [[0, 1]], 1: [[1, 0], [1, 0]]})
    assert counts == [{"10": 1}, {"01": 2}]


# ---------------------------------------------------------------------------
# job: status
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,expected",
    [
        ("queued", JobStatus.QUEUED),
        ("ongoing", JobStatus.RUNNING),
        ("finished", JobStatus.COMPLETED),
        ("cancelled", JobStatus.CANCELLED),
    ],
)
def test_job_status_mapping(mock_session, status, expected):
    """Each arnica job status maps to the corresponding qBraid ``JobStatus``."""
    result = {"0": [[1, 0]]} if status == "finished" else None
    mock_session.get_result.return_value = _result_payload(status, result=result)
    job = AQTJob("job-1", session=mock_session)
    assert job.status() == expected


def test_job_status_error_state(mock_session):
    """An error response maps to ``JobStatus.FAILED``."""
    mock_session.get_result.return_value = _result_payload("error", message="boom")
    job = AQTJob("job-1", session=mock_session)
    assert job.status() == JobStatus.FAILED


def test_job_cancel(mock_session):
    """``cancel`` delegates to ``session.cancel_job`` with the job id."""
    job = AQTJob("job-1", session=mock_session)
    job.cancel()
    mock_session.cancel_job.assert_called_once_with("job-1")


# ---------------------------------------------------------------------------
# job: execution time
# ---------------------------------------------------------------------------


def test_execution_time_s_from_timing_data(mock_session):
    """execution_time_s is the ongoing -> finished span of the arnica timing_data, in seconds."""
    mock_session.get_result.return_value = {
        "job": {
            "job_id": "00000000-0000-0000-0000-0000000000ab",
            "workspace_id": "ws",
            "resource_id": "res",
        },
        "response": {
            "status": "finished",
            "timing_data": [
                {"new_status": "queued", "timestamp": "2026-07-16T10:21:41.435142Z"},
                {"new_status": "ongoing", "timestamp": "2026-07-16T10:21:41.939164Z"},
                {"new_status": "finished", "timestamp": "2026-07-16T10:21:42.032645Z"},
            ],
            "result": {"0": [[1, 1, 1]]},
        },
    }
    job = AQTJob("00000000-0000-0000-0000-0000000000ab", session=mock_session)
    assert job.execution_time_s() == pytest.approx(0.093481)
    assert mock_session.get_result.call_args.kwargs == {"include_timing_data": True}


def test_execution_time_s_none_when_not_completed(mock_session):
    """execution_time_s returns None for a job that has not finished."""
    mock_session.get_result.return_value = _result_payload("ongoing")
    job = AQTJob("job-1", session=mock_session)
    assert job.execution_time_s() is None


def test_execution_time_s_raises_when_finished_without_timing(mock_session):
    """A finished job missing timing_data raises ``AQTJobError`` rather than returning None."""
    mock_session.get_result.return_value = _result_payload("finished", result={"0": [[1]]})
    job = AQTJob("job-1", session=mock_session)
    with pytest.raises(AQTJobError):
        job.execution_time_s()


# ---------------------------------------------------------------------------
# job: result
# ---------------------------------------------------------------------------


def test_job_result_success_reversed_counts(device, mock_session):
    """A finished job yields a successful ``Result`` with reversed (little-endian) counts."""
    mock_session.get_result.return_value = _result_payload(
        "finished",
        result={"0": [[1, 0], [1, 0], [0, 1]]},
        workspace_id="default",
        resource_id="sim1",
    )
    job = AQTJob("job-1", session=mock_session, device=device)
    result = job.result()
    assert result.success is True
    # [1, 0] -> "01", [0, 1] -> "10"
    assert result.data.get_counts() == {"01": 2, "10": 1}


def test_job_result_error_raises_aqt_job_error(mock_session):
    """A non-finished (error) response raises ``AQTJobError`` carrying the arnica message."""
    mock_session.get_result.return_value = _result_payload("error", message="calibration drift")
    job = AQTJob("job-1", session=mock_session)
    with pytest.raises(AQTJobError, match="calibration drift"):
        job.result()


def test_job_result_device_id_from_metadata(mock_session):
    """With no attached device, the result device id is derived from arnica job metadata."""
    mock_session.get_result.return_value = _result_payload(
        "finished", result={"0": [[0], [1]]}, workspace_id="ws", resource_id="res"
    )
    result = AQTJob("job-1", session=mock_session).result()
    assert result.device_id == "ws/res"


def test_job_session_none_fallback(monkeypatch):
    """``AQTJob(session=None)`` lazily builds a default ``AQTSession``."""
    sentinel = MagicMock(name="AQTSession()")
    monkeypatch.setattr("qbraid.runtime.aqt.provider.AQTSession", lambda: sentinel)
    assert AQTJob("job-1").session is sentinel

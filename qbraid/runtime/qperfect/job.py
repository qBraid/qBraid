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
Module defining QPerfect (MIMIQ) job class.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData, MeasCount

from .client import build_connection, resolve_token

if TYPE_CHECKING:
    from mimiqcircuits import MimiqConnection

# MIMIQ execution status (mimiqlink ``RequestInfo.status``) -> qBraid ``JobStatus``.
_STATUS_MAP = {
    "NEW": JobStatus.QUEUED,
    "RUNNING": JobStatus.RUNNING,
    "DONE": JobStatus.COMPLETED,
    "ERROR": JobStatus.FAILED,
    "CANCELED": JobStatus.CANCELLED,
}


class QPerfectJobError(QbraidRuntimeError):
    """Class for errors raised while processing a QPerfect job."""


def _histogram_to_counts(histogram: dict[Any, Any]) -> MeasCount:
    """Convert a MIMIQ ``QCSResults`` histogram to qBraid bitstring counts.

    The histogram maps each measured ``BitString`` to its number of occurrences. ``BitString.to01``
    orders qubits ``q0..q_{n-1}`` (qubit 0 first); each key is reversed so the bitstring follows
    qBraid's little-endian convention (qubit 0 as the least-significant / rightmost bit).
    """
    counts: MeasCount = {}
    for bitstring, count in histogram.items():
        key = bitstring.to01()[::-1]
        counts[key] = counts.get(key, 0) + int(count)
    return counts


class QPerfectJob(QuantumJob):
    """QPerfect (MIMIQ) job class."""

    def __init__(
        self,
        job_id: str,
        connection: Optional[MimiqConnection] = None,
        **kwargs,
    ):
        super().__init__(job_id=job_id, **kwargs)
        if connection is None:
            connection = build_connection(resolve_token(None))
        self._connection = connection

    @property
    def connection(self) -> MimiqConnection:
        """Return the MIMIQ connection used by this job."""
        return self._connection

    def status(self) -> JobStatus:
        """Return the current status of the QPerfect job.

        Uses a single ``requestInfo`` API call (the ``mimiqlink`` ``isJob*`` helpers each issue
        their own request, so they are not used here).
        """
        info = self._connection.connection.requestInfo(self.id)
        return _STATUS_MAP.get(info.status, JobStatus.UNKNOWN)

    def cancel(self) -> None:
        """Cancel the QPerfect job.

        Raises:
            QPerfectJobError: If the cancellation request fails — e.g. the job is already in a
                terminal state (and can no longer be cancelled) or the connection is unavailable.
        """
        try:
            self._connection.connection.stopExecution(self.id)
        except Exception as err:  # pylint: disable=broad-except
            raise QPerfectJobError(f"Failed to cancel job {self.id}: {err}") from err

    def result(self) -> Result:
        """Wait for the QPerfect job to finish and return its result."""
        self.wait_for_final_state()
        status = self.status()
        if status != JobStatus.COMPLETED:
            raise QPerfectJobError(
                f"Job {self.id} did not complete successfully (status={status.name})."
            )

        results = self._connection.get_results(self.id)
        if not isinstance(results, list):
            results = [results]
        counts = [_histogram_to_counts(result.histogram()) for result in results]
        measurement_counts: Union[MeasCount, list[MeasCount]] = (
            counts[0] if len(counts) == 1 else counts
        )
        data = GateModelResultData(measurement_counts=measurement_counts)
        device_id = self._device.id if self._device is not None else ""
        return Result(device_id=device_id, job_id=self.id, success=True, data=data)

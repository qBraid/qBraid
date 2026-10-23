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

import math
from typing import TYPE_CHECKING, Any

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError, ResourceNotFoundError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData, MeasCount

from .client import build_connection

if TYPE_CHECKING:
    from mimiqcircuits import MimiqConnection, QCSResults

# MIMIQ execution status (mimiqlink ``RequestInfo.status``) -> qBraid ``JobStatus``. Covers the
# full vocabulary mimiqlink publishes in ``RequestInfo.STATUS_COLORS``.
_STATUS_MAP: dict[str, JobStatus] = {
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


def accuracy_report(result: QCSResults) -> dict[str, Any]:
    """Return MIMIQ's account of how exact one circuit's counts are.

    An MPS run compresses the state to the job's bond dimension, so its counts can be approximate
    with nothing in them to say so. ``fidelity`` is the lowest of MIMIQ's per-execution fidelity
    lower bounds (1.0 is exact) and ``avgGateError`` the highest gate-error estimate. A value MIMIQ
    left unreported (NaN, or an empty name) is omitted rather than set to ``None``, and so is an
    aggregate when any execution's estimate is unreported: the rest would bound only some runs.
    """
    report: dict[str, Any] = {}
    fidelities = list(result.fidelities)
    if fidelities and all(math.isfinite(value) for value in fidelities):
        report["fidelity"] = min(fidelities)
        if len(fidelities) > 1:
            report["fidelityMean"] = sum(fidelities) / len(fidelities)
    gate_errors = list(result.avggateerrors)
    if gate_errors and all(math.isfinite(value) for value in gate_errors):
        report["avgGateError"] = max(gate_errors)
    if result.simulator:
        report["simulator"] = result.simulator
    if result.version:
        report["simulatorVersion"] = result.version
    return report


class QPerfectJob(QuantumJob):
    """QPerfect (MIMIQ) job class."""

    def __init__(
        self,
        job_id: str,
        connection: MimiqConnection | None = None,
        **kwargs,
    ):
        super().__init__(job_id=job_id, **kwargs)
        if connection is None:
            connection = build_connection()
        self._connection = connection

    @property
    def connection(self) -> MimiqConnection:
        """Return the MIMIQ connection used by this job."""
        return self._connection

    def _request_info(self) -> Any:
        """Return MIMIQ's execution record for this job.

        Raises:
            ResourceNotFoundError: If MIMIQ cannot return the record. An unknown job id surfaces
                here as a server error rather than a 404, so the vendor error is not inspected.
        """
        try:
            return self._connection.connection.requestInfo(self.id)
        except Exception as err:  # pylint: disable=broad-except
            raise ResourceNotFoundError(
                f"Could not retrieve execution details for job {self.id}: {err}"
            ) from err

    def status(self) -> JobStatus:
        """Return the current status of the QPerfect job.

        Uses a single ``requestInfo`` API call (the ``mimiqlink`` ``isJob*`` helpers each issue
        their own request, so they are not used here).

        Raises:
            QPerfectJobError: If MIMIQ reports a status outside the known mapping.
            ResourceNotFoundError: If MIMIQ has no execution record for this job id.
        """
        info = self._request_info()
        if info.status not in _STATUS_MAP:
            # ``RequestInfo.status`` falls back to the literal string "Unknown" when the payload
            # omits the field, so the message says "unrecognized" to keep that case readable.
            raise QPerfectJobError(
                f"MIMIQ reported an unrecognized job status '{info.status}'. "
                f"Expected one of: {', '.join(_STATUS_MAP)}"
            )
        return _STATUS_MAP[info.status]

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
        """Wait for the QPerfect job to finish and return its result.

        A circuit carrying no measurement instructions still returns counts: the emulator samples
        the final state over every qubit rather than rejecting the job.

        MIMIQ's :func:`accuracy_report` is in ``result.data.extra``. A batch carries one report per
        circuit, in submission order, under ``extra["accuracyReports"]``.

        Raises:
            QPerfectJobError: If the job reached a terminal state other than ``COMPLETED``. MIMIQ's
                own explanation (e.g. a backend that ran out of memory) is included when it gives
                one, since it usually names the fix.
        """
        self.wait_for_final_state()
        status = self.status()
        if status != JobStatus.COMPLETED:
            # Only FAILED and CANCELLED reach here: wait_for_final_state polls status(), which
            # rejects any state outside _STATUS_MAP before this point.
            outcome = "was cancelled" if status == JobStatus.CANCELLED else "failed"
            reason = self._request_info().get("errorMessage", None)
            detail = f": {reason}" if reason else "."
            raise QPerfectJobError(f"Job {self.id} {outcome}{detail}")

        results = self._connection.get_results(self.id)
        if not isinstance(results, list):
            results = [results]
        counts = [_histogram_to_counts(result.histogram()) for result in results]
        reports = [accuracy_report(result) for result in results]
        if len(results) == 1:
            data = GateModelResultData(measurement_counts=counts[0], **reports[0])
        else:
            data = GateModelResultData(measurement_counts=counts, accuracyReports=reports)
        device_id = self._device.id if self._device is not None else ""
        return Result(device_id=device_id, job_id=self.id, success=True, data=data)

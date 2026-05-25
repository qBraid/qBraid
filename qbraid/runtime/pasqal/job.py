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
Module defining Pasqal job class.

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import AnalogResultData

if TYPE_CHECKING:
    from pasqal_cloud import SDK as PasqalSDK
    from pasqal_cloud.batch import Batch

    from qbraid.runtime.pasqal.device import PasqalDevice

logger = logging.getLogger(__name__)


# Mapping from pasqal-cloud batch / job status strings to qBraid JobStatus.
# Pasqal exposes the same vocabulary for batch and job records, so a single
# table is reused for both lookups.
_PASQAL_STATUS_MAP: dict[str, JobStatus] = {
    "PENDING": JobStatus.QUEUED,
    "RUNNING": JobStatus.RUNNING,
    "DONE": JobStatus.COMPLETED,
    "ERROR": JobStatus.FAILED,
    "CANCELED": JobStatus.CANCELLED,
    "TIMED_OUT": JobStatus.FAILED,
    "PAUSED": JobStatus.QUEUED,
}

_TERMINAL_JOB_STATUSES = frozenset(
    {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    }
)


class PasqalJobError(QbraidRuntimeError):
    """Exception raised by :class:`PasqalJob`."""


def _map_pasqal_status(raw_status: str | None) -> JobStatus:
    """Map a pasqal-cloud status string to a qBraid :class:`JobStatus`.

    Returns :attr:`JobStatus.UNKNOWN` for ``None`` and any unrecognised value
    so the runtime never propagates a bare string further up.
    """
    if raw_status is None:
        return JobStatus.UNKNOWN
    return _PASQAL_STATUS_MAP.get(raw_status.upper(), JobStatus.UNKNOWN)


class PasqalJob(QuantumJob):
    """Pasqal Cloud Services job class.

    Each :class:`PasqalJob` is keyed by the underlying Pasqal *batch* id,
    which is the unit Pasqal Cloud schedules and reports on. For single-
    sequence submissions, the batch contains a single job, and
    :meth:`result` returns its counter result; for multi-sequence
    submissions, results from the batch's ordered jobs are aggregated.
    """

    def __init__(
        self,
        job_id: str,
        sdk: PasqalSDK | None = None,
        device: PasqalDevice | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Pasqal job.

        Args:
            job_id: The Pasqal Cloud batch id this job tracks.
            sdk: Authenticated ``pasqal_cloud.SDK`` instance. If omitted, the
                SDK is taken from ``device.sdk``; one of the two must be
                provided.
            device: The :class:`PasqalDevice` the job was submitted to.
            **kwargs: Forwarded to :class:`QuantumJob`.

        Raises:
            PasqalJobError: If neither ``sdk`` nor a usable ``device.sdk`` is
                available.
        """
        super().__init__(job_id=job_id, device=device, **kwargs)
        resolved_sdk = sdk if sdk is not None else getattr(device, "sdk", None)
        if resolved_sdk is None:
            raise PasqalJobError(
                "PasqalJob requires either an explicit `sdk` argument or a "
                "device that carries one."
            )
        self._sdk = resolved_sdk
        self._terminal_status: JobStatus | None = None

    @property
    def sdk(self) -> PasqalSDK:
        """Return the underlying ``pasqal_cloud.SDK`` instance."""
        return self._sdk

    def _fetch_batch(self) -> Batch:
        """Fetch the current Pasqal batch record, raising on transport error."""
        try:
            return self._sdk.get_batch(self.id)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise PasqalJobError(f"Unable to retrieve Pasqal batch {self.id}: {exc}") from exc

    def status(self) -> JobStatus:
        """Return the current status of the Pasqal job."""
        if self._terminal_status is not None:
            return self._terminal_status

        batch = self._fetch_batch()
        raw_status = getattr(batch, "status", None)
        job_status = _map_pasqal_status(raw_status)

        if job_status in _TERMINAL_JOB_STATUSES:
            self._terminal_status = job_status

        return job_status

    def cancel(self) -> None:
        """Cancel the underlying Pasqal batch."""
        try:
            self._sdk.cancel_batch(self.id)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise PasqalJobError(f"Failed to cancel Pasqal batch {self.id}: {exc}") from exc

    def result(self) -> Result[AnalogResultData]:
        """Return the result of the Pasqal job.

        Blocks until the batch reaches a terminal state, then aggregates the
        per-sequence counter results into an :class:`AnalogResultData`
        instance. For batches containing a single job, ``measurement_counts``
        is the job's counter dict directly; for multi-job batches, it is a
        list of counter dicts in submission order.

        Raises:
            PasqalJobError: If the batch finished in a non-completed state
                or carries no readable job results.
        """
        self.wait_for_final_state()
        batch = self._fetch_batch()

        if self.status() != JobStatus.COMPLETED:
            errors = getattr(batch, "errors", None)
            raise PasqalJobError(
                f"Pasqal batch {self.id} did not complete successfully: "
                f"status={getattr(batch, 'status', 'UNKNOWN')}, errors={errors}"
            )

        ordered_jobs = list(getattr(batch, "ordered_jobs", []) or [])
        if not ordered_jobs:
            raise PasqalJobError(f"No jobs found on Pasqal batch {self.id}.")

        counter_results: list[dict[str, int]] = []
        for job in ordered_jobs:
            counts = self._extract_counts(job)
            counter_results.append(counts)

        measurement_counts = counter_results[0] if len(counter_results) == 1 else counter_results
        device_id = self._device.id if self._device else "pasqal"

        return Result[AnalogResultData](
            device_id=device_id,
            job_id=self.id,
            success=True,
            data=AnalogResultData(measurement_counts=measurement_counts),
        )

    @staticmethod
    def _extract_counts(job: Any) -> dict[str, int]:
        """Extract a bitstring-counter dict from a pasqal-cloud Job record.

        Prefers ``Job.result`` (already the ``"counter"`` slice of the full
        result), falling back to ``Job.full_result['counter']``.
        """
        counts = getattr(job, "result", None)
        if counts is None:
            full_result = getattr(job, "full_result", None)
            if isinstance(full_result, dict):
                counts = full_result.get("counter")
        if counts is None:
            raise PasqalJobError(
                f"Pasqal job {getattr(job, 'id', '?')} has no counter result available."
            )
        return dict(counts)

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

import functools
import warnings
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import AnalogResultData

if TYPE_CHECKING:
    from pasqal_cloud.batch import Batch
    from pasqal_cloud.batch import Job as PasqalBatchJob
    from pasqal_cloud.utils.constants import BatchStatus

    from qbraid.runtime.pasqal.device import PasqalClient, PasqalDevice


def _status_map() -> dict[BatchStatus, JobStatus]:
    """Map every ``pasqal_cloud`` batch status to a qBraid :class:`JobStatus`.

    Keyed on the vendor's ``BatchStatus`` members rather than their string
    values, so a release that renames or adds a status fails the
    exhaustiveness test instead of drifting silently.
    """
    # pylint: disable-next=import-outside-toplevel
    from pasqal_cloud.utils.constants import BatchStatus as Status

    return {
        Status.PENDING: JobStatus.QUEUED,
        Status.RUNNING: JobStatus.RUNNING,
        Status.DONE: JobStatus.COMPLETED,
        Status.ERROR: JobStatus.FAILED,
        Status.CANCELED: JobStatus.CANCELLED,
        Status.TIMED_OUT: JobStatus.FAILED,
    }


# Pasqal documents ``PAUSED`` as a batch status, but ``BatchStatus`` does not
# include it. A paused batch has not finished, so it reads as queued.
_UNENUMERATED_STATUSES: dict[str, JobStatus] = {"PAUSED": JobStatus.QUEUED}


class PasqalJobError(QbraidRuntimeError):
    """Exception raised by :class:`PasqalJob`."""


def _warn_sdk_renamed(owner: str) -> None:
    """Warn that ``<owner>.sdk`` / ``sdk=`` is now ``client``."""
    warnings.warn(
        f"{owner}'s `sdk` is deprecated and will be removed in a future release; use `client`.",
        DeprecationWarning,
        stacklevel=3,
    )


@functools.cache
def _pasqal_cloud_errors() -> tuple[type[BaseException], ...]:
    """Return ``Exception`` plus every error class ``pasqal_cloud.errors`` defines.

    Most pasqal-cloud errors, including the ones raised when a batch is rejected, not
    found or cannot be cancelled, derive from ``BaseException``, so ``except Exception``
    does not catch them. Catch this tuple wherever a pasqal-cloud call is wrapped.
    """
    # pylint: disable-next=import-outside-toplevel
    from pasqal_cloud import errors

    return (
        Exception,
        *(
            cls
            for cls in vars(errors).values()
            if isinstance(cls, type)
            and issubclass(cls, BaseException)
            and not issubclass(cls, Exception)
            and cls.__module__ == errors.__name__
        ),
    )


def _map_pasqal_status(raw_status: str) -> JobStatus:
    """Map a pasqal-cloud batch status string to a qBraid :class:`JobStatus`.

    Raises:
        PasqalJobError: If Pasqal reports a status qBraid does not know.
            ``UNKNOWN`` is not terminal, so returning it would leave
            :meth:`PasqalJob.wait_for_final_state` polling a finished job
            until it timed out.
    """
    # pylint: disable-next=import-outside-toplevel
    from pasqal_cloud.utils.constants import BatchStatus as Status

    if raw_status in _UNENUMERATED_STATUSES:
        return _UNENUMERATED_STATUSES[raw_status]
    try:
        return _status_map()[Status(raw_status)]
    except (ValueError, KeyError) as exc:
        raise PasqalJobError(f"Unrecognized Pasqal batch status: {raw_status!r}.") from exc


def _parse_timestamp(value: str) -> datetime:
    """Parse a Pasqal ISO-8601 timestamp into a timezone-aware datetime (UTC if unmarked).

    Raises:
        PasqalJobError: If the value is not an ISO-8601 timestamp.
    """
    try:
        # ``fromisoformat`` only accepts a ``Z`` suffix from Python 3.11.
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise PasqalJobError(f"Unrecognized Pasqal timestamp: {value!r}.") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _time_stamps(batch: Batch) -> dict[str, Any]:
    """Return the batch's creation, start and end times, and execution time in ms.

    Pasqal reports ISO-8601 strings; ``startedAt``, ``endedAt`` and
    ``executionDuration`` are ``None`` until the batch has started and ended.
    """
    started = _parse_timestamp(batch.start_datetime) if batch.start_datetime else None
    ended = _parse_timestamp(batch.end_datetime) if batch.end_datetime else None
    duration = int((ended - started).total_seconds() * 1000) if started and ended else None
    return {
        "createdAt": _parse_timestamp(batch.created_at),
        "startedAt": started,
        "endedAt": ended,
        "executionDuration": duration,
    }


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
        client: PasqalClient | None = None,
        device: PasqalDevice | None = None,
        *,
        sdk: PasqalClient | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Pasqal job.

        Args:
            job_id: The Pasqal Cloud batch id this job tracks.
            client: Authenticated ``pasqal_cloud`` client. If omitted, the
                client is taken from ``device.client``; one of the two must be
                provided.
            device: The :class:`PasqalDevice` the job was submitted to.
            sdk: Deprecated alias for ``client``.
            **kwargs: Forwarded to :class:`QuantumJob`.

        Raises:
            PasqalJobError: If neither ``client`` nor a usable ``device.client``
                is available.
        """
        super().__init__(job_id=job_id, device=device, **kwargs)
        if sdk is not None:
            _warn_sdk_renamed("PasqalJob")
            client = client if client is not None else sdk
        if client is None and device is not None:
            client = device.client
        if client is None:
            raise PasqalJobError(
                "PasqalJob requires either an explicit `client` argument or a "
                "device that carries one."
            )
        self._client = client
        self._terminal_status: JobStatus | None = None

    @property
    def client(self) -> PasqalClient:
        """Return the underlying ``pasqal_cloud`` client."""
        return self._client

    @property
    def sdk(self) -> PasqalClient:
        """Deprecated alias for :attr:`client`."""
        _warn_sdk_renamed("PasqalJob")
        return self._client

    def _fetch_batch(self) -> Batch:
        """Fetch the current Pasqal batch record, raising on transport error."""
        try:
            return self._client.get_batch(str(self.id))
        except _pasqal_cloud_errors() as exc:
            raise PasqalJobError(f"Unable to retrieve Pasqal batch {self.id}: {exc}") from exc

    def status(self) -> JobStatus:
        """Return the current status of the Pasqal job."""
        if self._terminal_status is not None:
            return self._terminal_status

        batch = self._fetch_batch()
        raw_status = batch.status
        job_status = _map_pasqal_status(raw_status)

        if job_status in JobStatus.terminal_states():
            self._terminal_status = job_status

        return job_status

    def cancel(self) -> None:
        """Cancel the underlying Pasqal batch."""
        try:
            self._client.cancel_batch(str(self.id))
        except _pasqal_cloud_errors() as exc:
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
            raise PasqalJobError(
                f"Pasqal batch {self.id} did not complete successfully: " f"status={batch.status}"
            )

        ordered_jobs = list(batch.ordered_jobs)
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
            time_stamps=_time_stamps(batch),
        )

    @staticmethod
    def _extract_counts(job: PasqalBatchJob) -> dict[str, int]:
        """Extract a bitstring-counter dict from a pasqal-cloud Job record.

        Prefers ``Job.result`` (already the ``"counter"`` slice of the full
        result), falling back to ``Job.full_result['counter']``.
        """
        try:
            counts = job.result
            if counts is None:
                full_result = job.full_result
                if isinstance(full_result, dict):
                    counts = full_result.get("counter")
        except _pasqal_cloud_errors() as exc:  # the results are downloaded on first access
            raise PasqalJobError(
                f"Unable to download the results of Pasqal job {job.id}: {exc}"
            ) from exc
        if counts is None:
            raise PasqalJobError(f"Pasqal job {job.id} has no counter result available.")
        return dict(counts)

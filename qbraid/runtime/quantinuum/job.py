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
Module defining Quantinuum job class.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbraid._logging import logger
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

from ._transport import ensure_bounded_client

if TYPE_CHECKING:
    from qnexus.models.job_status import JobStatus as NexusJobStatus
    from qnexus.models.references import ExecuteJobRef

    from qbraid.runtime.quantinuum.device import QuantinuumDevice

#: Every member of ``qnexus.models.job_status.JobStatusEnum``, keyed by value so
#: the module does not need qnexus imported to be defined. The two terminal
#: failure states NEXUS reports besides ``ERROR`` matter most here: an unmapped
#: status falls through to ``UNKNOWN``, which is not terminal, so a job that has
#: actually stopped would be polled until the caller's own timeout.
#:
#: - ``SUBMITTED`` is the state a job enters the moment NEXUS accepts it, before
#:   the device queues it, so it is the first status most jobs ever report.
#: - ``RETRYING`` means NEXUS is re-attempting the job; it has produced no
#:   results, so it maps to ``QUEUED`` rather than ``RUNNING``.
#: - ``TERMINATED`` (stopped by the platform) and ``DEPLETED`` (credits
#:   exhausted) are terminal failures.
_QUANTINUUM_STATUS_MAP: dict[str, JobStatus] = {
    "COMPLETED": JobStatus.COMPLETED,
    "ERROR": JobStatus.FAILED,
    "TERMINATED": JobStatus.FAILED,
    "DEPLETED": JobStatus.FAILED,
    "CANCELLED": JobStatus.CANCELLED,
    "CANCELLING": JobStatus.CANCELLING,
    "SUBMITTED": JobStatus.QUEUED,
    "QUEUED": JobStatus.QUEUED,
    "RETRYING": JobStatus.QUEUED,
    "RUNNING": JobStatus.RUNNING,
}


class QuantinuumJobError(QbraidRuntimeError):
    """Class for errors raised while processing a Quantinuum job."""


def _map_quantinuum_status(last_status: str | None) -> JobStatus:
    """Map a qnexus job status value to a qBraid :class:`JobStatus`."""
    if last_status is None:
        return JobStatus.UNKNOWN
    return _QUANTINUUM_STATUS_MAP.get(last_status, JobStatus.UNKNOWN)


class QuantinuumJob(QuantumJob):
    """Quantinuum NEXUS job class."""

    def __init__(
        self,
        job_id: str,
        device: QuantinuumDevice | None = None,
        job: ExecuteJobRef | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(job_id=job_id, device=device, **kwargs)
        self._job = job
        self._status_detail: NexusJobStatus | None = None

    def _get_ref(self) -> ExecuteJobRef:
        """Return the cached qnexus job reference, or look it up by ID."""
        if self._job is not None:
            return self._job
        try:
            # pylint: disable-next=import-outside-toplevel
            import qnexus as qnx

            ensure_bounded_client()
            self._job = qnx.jobs.get(id=self.id)
            return self._job
        except Exception as exc:
            raise QuantinuumJobError(f"Unable to retrieve Quantinuum job {self.id}") from exc

    def status(self) -> JobStatus:
        """Return the current status of the Quantinuum job.

        Queries NEXUS for a fresh status rather than reading ``last_status``
        off the job reference. That field is a plain snapshot taken when the
        reference was built, so a job object held across a run -- the ordinary
        ``job = device.run(...)`` case -- would report its submission-time
        status forever and never observe completion.
        """
        if self._cache_metadata.get("status") in JobStatus.terminal_states():
            return self._cache_metadata["status"]

        # pylint: disable-next=import-outside-toplevel
        import qnexus as qnx

        try:
            ref = self._get_ref()
            ensure_bounded_client()
            detail = qnx.jobs.status(ref)
        except Exception as exc:
            raise QuantinuumJobError(f"Unable to retrieve job status for {self.id}") from exc

        status = _map_quantinuum_status(detail.status.value)
        if status == JobStatus.FAILED:
            logger.error(
                "Quantinuum job %s failed: %s",
                self.id,
                detail.error_detail or detail.message or "no error message",
            )

        self._status_detail = detail
        self._cache_metadata["status"] = status
        return status

    def _resolve_device_id(self, ref: ExecuteJobRef) -> str:
        """Resolve the target device name for a job.

        Prefers the device this job was constructed with, then tries to read
        the device name from the NEXUS job's ``backend_config`` when it is a
        :class:`~quantinuum_schemas.models.backend_config.QuantinuumConfig`
        (other ``BackendConfig`` subclasses do not expose ``device_name``).
        Falls back to the generic ``"quantinuum"`` label if neither is set.
        """
        # pylint: disable-next=import-outside-toplevel
        from quantinuum_schemas.models.backend_config import QuantinuumConfig

        if self._device is not None:
            return self._device.id
        backend_config = ref.backend_config
        if isinstance(backend_config, QuantinuumConfig):
            return backend_config.device_name
        return "quantinuum"

    def cancel(self) -> None:
        """Cancel the Quantinuum job."""
        # pylint: disable-next=import-outside-toplevel
        import qnexus as qnx

        try:
            ensure_bounded_client()
            qnx.jobs.cancel(self._get_ref())
        except Exception as exc:
            raise QuantinuumJobError(f"Failed to cancel Quantinuum job {self.id}") from exc

    def execution_time_s(self) -> float | None:
        """Return the wall-clock execution time of the job in seconds.

        Computed from the NEXUS status timestamps
        (``completed_time - running_time``). This duration reflects the total
        time the job spent in the "running" phase on the service and may
        include queueing, calibration, and other backend checks in addition
        to on-device execution. qnexus does not currently expose a more
        granular, on-device-only metric.

        The timestamps come from the status fetched by :meth:`status`, not from
        the job reference's snapshot, which is fixed at the moment the
        reference was built and so carries no completion time at all.

        Returns:
            The execution time in seconds, or ``None`` if the job has not
            completed.

        Raises:
            QuantinuumJobError: If the job is completed but timing details
                are unavailable.
        """
        if self.status() != JobStatus.COMPLETED:
            return None
        detail = self._status_detail
        if detail is None:
            raise QuantinuumJobError(
                f"Execution time not available for {self.id}: status detail is missing"
            )
        completed_time = detail.completed_time
        running_time = detail.running_time
        if completed_time is None or running_time is None:
            raise QuantinuumJobError(
                f"Execution time not available for {self.id}: "
                "completed_time or running_time is missing"
            )
        return (completed_time - running_time).total_seconds()

    def result(self) -> Result[GateModelResultData]:
        """Return the result of the Quantinuum job."""
        # pylint: disable-next=import-outside-toplevel
        import qnexus as qnx

        # pylint: disable-next=import-outside-toplevel
        from pytket.circuit import BasisOrder

        self.wait_for_final_state()

        if self.status() == JobStatus.FAILED:
            detail = self._status_detail
            message = (
                (detail.error_detail or detail.message) if detail is not None else None
            ) or "no error message"
            raise QuantinuumJobError(f"Quantinuum job {self.id} failed: {message}")

        ref = self._get_ref()
        try:
            ensure_bounded_client()
            results = qnx.jobs.results(ref)
        except Exception as exc:
            raise QuantinuumJobError(
                f"Failed to fetch results for Quantinuum job {self.id}"
            ) from exc

        if not results:
            raise QuantinuumJobError(f"No results available for Quantinuum job {self.id}")

        # Quantinuum / pytket use least-significant-bit-first ordering by default.
        # Convert to most-significant-bit-first (dlo = descending lexicographic order)
        # for consistency with other qBraid providers.
        all_counts: list[dict[str, int]] = []
        for result_item in results:
            counts = result_item.download_result().get_counts(basis=BasisOrder.dlo)
            all_counts.append({"".join(map(str, k)): v for k, v in counts.items()})

        measurement_counts = all_counts[0] if len(all_counts) == 1 else all_counts
        device_id = self._resolve_device_id(ref)

        return Result[GateModelResultData](
            device_id=device_id,
            job_id=self.id,
            success=True,
            data=GateModelResultData(measurement_counts=measurement_counts),
        )

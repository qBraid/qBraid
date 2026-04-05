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
Module defining OriginQ job class.

"""
import logging
from typing import Any, Optional

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

logger = logging.getLogger(__name__)

_STATUS_LOOKUP = {
    "FINISH": JobStatus.COMPLETED,
    "FINISHED": JobStatus.COMPLETED,
    "COMPLETED": JobStatus.COMPLETED,
    "WAITING": JobStatus.QUEUED,
    "QUEUING": JobStatus.QUEUED,
    "QUEUED": JobStatus.QUEUED,
    "COMPUTING": JobStatus.RUNNING,
    "RUNNING": JobStatus.RUNNING,
    "EXECUTING": JobStatus.RUNNING,
    "FAILED": JobStatus.FAILED,
    "ERROR": JobStatus.FAILED,
}


class OriginJobError(QbraidRuntimeError):
    """Class for errors raised while processing an OriginQ job."""


def _normalize_status(origin_status: Any) -> str:
    """Convert various SDK status representations to a comparable uppercase string."""
    if hasattr(origin_status, "name"):
        candidate = origin_status.name
    elif hasattr(origin_status, "value"):
        candidate = origin_status.value
    else:
        candidate = origin_status

    normalized = str(candidate).strip().upper()
    if normalized.startswith("JOBSTATUS."):
        normalized = normalized.split(".", 1)[1]
    if normalized.startswith("JOB_"):
        normalized = normalized[4:]
    return normalized


def _map_status(origin_status: Any) -> JobStatus:
    """Map OriginQ status to qBraid JobStatus."""
    normalized = _normalize_status(origin_status)
    return _STATUS_LOOKUP.get(normalized, JobStatus.UNKNOWN)


class OriginJob(QuantumJob):
    """OriginQ QCloud job class."""

    def __init__(
        self,
        job_id: str,
        *,
        device: Optional[Any] = None,
        backend_job: Optional[Any] = None,
        service: Optional[Any] = None,
        **kwargs,
    ) -> None:
        super().__init__(job_id=job_id, device=device, **kwargs)
        self._backend_job = backend_job
        self._service = service

    def _get_backend_job(self):
        """Return the cached backend job, or reconstruct it from the job ID."""
        if self._backend_job is not None:
            return self._backend_job
        try:
            # pylint: disable-next=import-outside-toplevel
            from qbraid.runtime.origin.provider import _get_qcloud_job

            self._backend_job = _get_qcloud_job(self.id, service=self._service)
        except Exception as exc:
            raise OriginJobError(f"Unable to retrieve OriginQ job {self.id}") from exc
        return self._backend_job

    def status(self) -> JobStatus:
        """Return the current status of the OriginQ job."""
        try:
            raw_status = self._get_backend_job().status()
        except Exception:
            logger.debug("Unable to retrieve job status for %s", self.id, exc_info=True)
            return JobStatus.UNKNOWN
        return _map_status(raw_status)

    def cancel(self) -> None:
        """Cancel the OriginQ job. Not supported by the QCloud SDK."""
        raise OriginJobError("OriginQ does not support job cancellation.")

    def result(self) -> Result:
        """Return the result of the OriginQ job."""
        self.wait_for_final_state()
        backend_job = self._get_backend_job()

        try:
            result_obj = backend_job.result()
        except Exception as exc:
            raise OriginJobError(f"Failed to fetch results for OriginQ job {self.id}") from exc

        counts = result_obj.get_counts()
        if not counts:
            try:
                counts_list = result_obj.get_counts_list()
            except Exception:
                counts_list = []
            if counts_list:
                counts = counts_list[0]
        counts = counts or {}

        normalized = {str(key): int(value) for key, value in counts.items()}
        device_id = self._device.profile.device_id if self._device else "origin"

        return Result(
            device_id=device_id,
            job_id=self.id,
            success=True,
            data=GateModelResultData(measurement_counts=normalized),
        )

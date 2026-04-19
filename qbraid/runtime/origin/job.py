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
Module defining OriginQ job class.

"""
from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Any

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    from pyqpanda3.qcloud import QCloudJob, QCloudResult, QCloudService
    from pyqpanda3.qcloud.qcloud import JobStatus as OriginJobStatus

    from qbraid.runtime.origin.device import OriginDevice

logger = logging.getLogger(__name__)

_ORIGIN_STATUS_MAP: dict[str, JobStatus] = {
    "FINISHED": JobStatus.COMPLETED,
    "WAITING": JobStatus.QUEUED,
    "QUEUING": JobStatus.QUEUED,
    "COMPUTING": JobStatus.RUNNING,
    "FAILED": JobStatus.FAILED,
}


def _map_origin_status(origin_status: OriginJobStatus) -> JobStatus:
    """Convert an OriginQ SDK JobStatus enum to a qBraid JobStatus.

    The pyqpanda3 JobStatus enum members have a ``name`` attribute
    (e.g. ``"FINISHED"``). We map via the string name so that the
    SDK enum does not need to be imported at module level.

    Raises:
        ValueError: If the status name is not in the known mapping.
    """
    name = origin_status.name
    if name not in _ORIGIN_STATUS_MAP:
        raise ValueError(
            f"Unknown OriginQ job status '{name}'. "
            f"Expected one of: {', '.join(_ORIGIN_STATUS_MAP)}"
        )
    return _ORIGIN_STATUS_MAP[name]


class OriginJobError(QbraidRuntimeError):
    """Class for errors raised while processing an OriginQ job."""


class OriginJob(QuantumJob):
    """OriginQ QCloud job class."""

    def __init__(
        self,
        job_id: str,
        device: OriginDevice | None = None,
        job: QCloudJob | None = None,
        service: QCloudService | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(job_id=job_id, device=device, **kwargs)
        self._job = self._get_job(job_id, job, service)

    @staticmethod
    def _get_job(
        job_id: str, job: QCloudJob | None = None, service: QCloudService | None = None
    ) -> QCloudJob:
        """Return the QCloud job, or reconstruct it from the job ID."""
        if job is not None:
            if job.job_id() != job_id:
                raise OriginJobError(f"QCloud job {job.job_id()} does not match job ID {job_id}")
            return job

        try:
            # pylint: disable=import-outside-toplevel
            from pyqpanda3.qcloud import QCloudJob as _QCloudJob
            from pyqpanda3.qcloud import QCloudService as _QCloudService

            # pylint: enable=import-outside-toplevel

            if service is None:
                # QCloudService must be initialized before QCloudJob
                # in order to correctly configure HTTP URL
                _QCloudService(os.getenv("ORIGIN_API_KEY"))

            return _QCloudJob(job_id)
        except Exception as exc:
            raise OriginJobError(f"Unable to retrieve OriginQ job {job_id}") from exc

    def status(self) -> JobStatus:
        """Return the current status of the OriginQ job."""
        if self._cache_metadata.get("status") in JobStatus.terminal_states():
            return self._cache_metadata["status"]

        try:
            origin_status = self._job.status()
        except Exception as exc:
            raise OriginJobError(f"Unable to retrieve job status for {self.id}") from exc

        status = _map_origin_status(origin_status)
        self._cache_metadata["status"] = status
        return status

    def cancel(self) -> None:
        """Cancel the OriginQ job. Not supported by the QCloud SDK."""
        raise OriginJobError("OriginQ does not support job cancellation.")

    @staticmethod
    def _extract_results(
        origin_result: QCloudResult,
    ) -> tuple[
        dict[str, int] | list[dict[str, int]] | None,
        dict[str, float] | list[dict[str, float]] | None,
    ]:
        """Extract measurement counts and probabilities from a QCloudResult.

        For single-circuit jobs, returns a single dict.
        For batch jobs (multiple circuits), returns a list of dicts.

        The pyqpanda3 SDK raises ``RuntimeError`` when the result type
        doesn't match the accessor (e.g. calling ``get_counts_list`` on
        a probability-based result), so we attempt each independently.
        """
        counts: dict[str, int] | list[dict[str, int]] | None = None
        probabilities: dict[str, float] | list[dict[str, float]] | None = None

        try:
            counts_list: list[dict[str, int]] = origin_result.get_counts_list()
            if counts_list:
                counts = counts_list[0] if len(counts_list) == 1 else counts_list
        except RuntimeError as exc:
            logger.error("Failed to extract counts from OriginQ job: %s", exc)

        try:
            probs_list: list[dict[str, float]] = origin_result.get_probs_list()
            if probs_list:
                probabilities = probs_list[0] if len(probs_list) == 1 else probs_list
        except RuntimeError as exc:
            logger.error("Failed to extract probabilities from OriginQ job: %s", exc)

        return counts, probabilities

    def result(self) -> Result[GateModelResultData]:
        """Return the result of the OriginQ job."""
        self.wait_for_final_state()

        try:
            origin_result: QCloudResult = self._job.result()
        except Exception as exc:
            raise OriginJobError(f"Failed to fetch results for OriginQ job {self.id}") from exc

        metadata: dict[str, Any] = json.loads(origin_result.origin_data())
        success: bool = metadata.pop("success", self.status() == JobStatus.COMPLETED)

        counts, probabilities = self._extract_results(origin_result)
        device_id = self._device.id if self._device else "origin"

        return Result[GateModelResultData](
            device_id=device_id,
            job_id=self.id,
            success=success,
            data=GateModelResultData(
                measurement_counts=counts,
                measurement_probabilities=probabilities,
            ),
            **metadata,
        )

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

import logging
from typing import TYPE_CHECKING, Any

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    from qnexus.models.references import ExecuteJobRef

    from qbraid.runtime.quantinuum.device import QuantinuumDevice

logger = logging.getLogger(__name__)

_QUANTINUUM_STATUS_MAP: dict[str, JobStatus] = {
    "COMPLETED": JobStatus.COMPLETED,
    "ERROR": JobStatus.FAILED,
    "CANCELLED": JobStatus.CANCELLED,
    "QUEUED": JobStatus.QUEUED,
    "RUNNING": JobStatus.RUNNING,
    "INITIALIZING": JobStatus.INITIALIZING,
}


class QuantinuumJobError(QbraidRuntimeError):
    """Class for errors raised while processing a Quantinuum job."""


def _map_quantinuum_status(last_status: str | None) -> JobStatus:
    """Map a qnexus ``last_status`` string to a qBraid :class:`JobStatus`."""
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

    def _get_ref(self) -> ExecuteJobRef:
        """Return the cached qnexus job reference, or look it up by ID."""
        if self._job is not None:
            return self._job
        try:
            # pylint: disable-next=import-outside-toplevel
            import qnexus as qnx

            self._job = qnx.jobs.get(id=self.id)
            return self._job
        except Exception as exc:
            raise QuantinuumJobError(f"Unable to retrieve Quantinuum job {self.id}") from exc

    def status(self) -> JobStatus:
        """Return the current status of the Quantinuum job."""
        if self._cache_metadata.get("status") in JobStatus.terminal_states():
            return self._cache_metadata["status"]

        try:
            ref = self._get_ref()
            last_status = getattr(ref, "last_status", None)
        except Exception as exc:
            raise QuantinuumJobError(f"Unable to retrieve job status for {self.id}") from exc

        status = _map_quantinuum_status(last_status)
        if status == JobStatus.FAILED:
            last_message = getattr(ref, "last_message", None)
            if last_message:
                logger.error("Quantinuum job %s failed: %s", self.id, last_message)

        self._cache_metadata["status"] = status
        return status

    def _resolve_device_id(self, ref: ExecuteJobRef) -> str:
        """Resolve the target device name for a job.

        Prefers the device this job was constructed with, then tries to read
        the device name from the NEXUS job's ``backend_config_store`` (set to
        a ``QuantinuumConfig`` when the job was dispatched via qBraid).
        Falls back to the generic ``"quantinuum"`` label if neither is set.
        """
        if self._device is not None:
            return self._device.id
        backend_config = getattr(ref, "backend_config_store", None)
        device_name = getattr(backend_config, "device_name", None)
        if device_name:
            return str(device_name)
        return "quantinuum"

    def cancel(self) -> None:
        """Cancel the Quantinuum job."""
        # pylint: disable-next=import-outside-toplevel
        import qnexus as qnx

        try:
            qnx.jobs.cancel(self._get_ref())
        except Exception as exc:
            raise QuantinuumJobError(f"Failed to cancel Quantinuum job {self.id}") from exc

    def execution_time_s(self) -> float | None:
        """Return the wall-clock execution time of the job in seconds.

        Computed from the NEXUS ``last_status_detail`` timestamps
        (``completed_time - running_time``). This duration reflects the total
        time the job spent in the "running" phase on the service and may
        include queueing, calibration, and other backend checks in addition
        to on-device execution. qnexus does not currently expose a more
        granular, on-device-only metric.

        Returns:
            The execution time in seconds, or ``None`` if the job has not
            completed.

        Raises:
            QuantinuumJobError: If the job is completed but timing details
                are unavailable.
        """
        if self.status() != JobStatus.COMPLETED:
            return None
        ref = self._get_ref()
        last_status_detail = getattr(ref, "last_status_detail", None)
        if last_status_detail is None:
            raise QuantinuumJobError(
                f"Execution time not available for {self.id}: last_status_detail is missing"
            )
        completed_time = getattr(last_status_detail, "completed_time", None)
        running_time = getattr(last_status_detail, "running_time", None)
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
            ref = self._get_ref()
            last_message = getattr(ref, "last_message", None)
            raise QuantinuumJobError(
                f"Quantinuum job {self.id} failed: {last_message or 'no error message'}"
            )

        ref = self._get_ref()
        try:
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

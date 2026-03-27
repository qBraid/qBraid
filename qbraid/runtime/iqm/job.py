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

# pylint:disable=invalid-name

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from qbraid_core._import import LazyLoader

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

from ._qiskit import format_measurement_results

if TYPE_CHECKING:
    import qbraid.runtime.iqm

qbraid_rt_iqm: qbraid.runtime.iqm = LazyLoader("qbraid_rt_iqm", globals(), "qbraid.runtime.iqm")


class IQMJobError(QbraidRuntimeError):
    """Class for errors raised while processing an IQM job."""


class IQMJob(QuantumJob):
    """IQM job class."""

    def __init__(
        self,
        job_id: str,
        session: Optional[qbraid.runtime.iqm.IQMSession] = None,
        job: Any = None,
        **kwargs,
    ):
        super().__init__(job_id=job_id, **kwargs)
        self._session = session or qbraid_rt_iqm.IQMSession()
        self._job = job

    @property
    def session(self) -> qbraid.runtime.iqm.IQMSession:
        """Return the IQM session."""
        return self._session

    @staticmethod
    def _raw_status(status: Any) -> str:
        if hasattr(status, "value"):
            return str(status.value).lower()
        return str(status).lower()

    @classmethod
    def _map_status(cls, status: Any) -> JobStatus:
        """Convert an IQM job status to a qBraid job status."""
        status_name = cls._raw_status(status)
        status_map = {
            "waiting": JobStatus.QUEUED,
            "processing": JobStatus.RUNNING,
            "completed": JobStatus.COMPLETED,
            "failed": JobStatus.FAILED,
            "cancelled": JobStatus.CANCELLED,
        }
        return status_map.get(status_name, JobStatus.UNKNOWN)

    @staticmethod
    def _job_data(job: Any) -> Any:
        return getattr(job, "data", job)

    @classmethod
    def _job_status(cls, job: Any) -> Any:
        data = cls._job_data(job)
        return getattr(job, "status", getattr(data, "status", None))

    def _get_job(self, refresh: bool = False) -> Any:
        if refresh or self._job is None:
            self._job = self.session.get_job(self.id)
        return self._job

    @staticmethod
    def _stringify_many(items: list[Any]) -> list[str]:
        return [str(item) for item in items]

    def _resolve_device_id(self) -> str:
        """Resolve the device identifier for the current job."""
        if self._device is not None:
            return self.device.id

        cached_device_id = self._cache_metadata.get("device_id")
        if cached_device_id is not None:
            return cached_device_id

        static_architecture = self.session.get_static_quantum_architecture()
        device_id = (
            self.session.quantum_computer
            or getattr(static_architecture, "dut_label", None)
            or self.session.url
        )
        self._cache_metadata["device_id"] = device_id
        return device_id

    def status(self) -> JobStatus:
        """Return the current status of the IQM job."""
        job = self._get_job(refresh=True)
        status = self._map_status(self._job_status(job))
        self._cache_metadata["status"] = status
        return status

    def metadata(self) -> dict[str, Any]:
        """Store and return metadata for the IQM job."""
        job = self._get_job(refresh=not self.is_terminal_state())
        job_data = self._job_data(job)
        messages = self._stringify_many(getattr(job_data, "messages", []))
        errors = self._stringify_many(getattr(job_data, "errors", []))
        compilation = getattr(job_data, "compilation", None)

        self._cache_metadata.update(
            {
                "device_id": self._resolve_device_id(),
                "messages": messages,
                "errors": errors,
                "queue_position": getattr(job_data, "queue_position", None),
                "timeline": getattr(job_data, "timeline", []),
                "status": self._map_status(self._job_status(job)),
                "calibration_set_id": (
                    getattr(compilation, "calibration_set_id", None) if compilation else None
                ),
            }
        )
        return self._cache_metadata

    def cancel(self) -> None:
        """Cancel the IQM job."""
        self.session.cancel_job(self.id)

    def result(self) -> Result:
        """Return the result of the IQM job."""
        self.wait_for_final_state()
        job = self._get_job(refresh=True)
        job_data = self._job_data(job)
        status = self._map_status(self._job_status(job))

        if status != JobStatus.COMPLETED:
            messages = self._stringify_many(getattr(job_data, "messages", []))
            errors = self._stringify_many(getattr(job_data, "errors", []))
            details = "; ".join(errors or messages) or "No additional error details returned by IQM."
            raise IQMJobError(
                f"Job {self.id} finished with status '{self._raw_status(self._job_status(job))}': {details}"
            )

        measurement_batch = self.session.get_job_measurements(self.id)
        formatted_results = [format_measurement_results(measurements) for measurements in measurement_batch]

        measurement_counts = [counts for _, _, counts in formatted_results]
        measurements = [shot_data for _, shot_data, _ in formatted_results]

        if self._cache_metadata.get("circuit_count", 1) == 1 and len(formatted_results) == 1:
            measurement_counts = measurement_counts[0]
            measurements = measurements[0]

        compilation = getattr(job_data, "compilation", None)
        data = GateModelResultData(
            measurement_counts=measurement_counts,
            measurements=measurements,
        )
        return Result(
            device_id=self._resolve_device_id(),
            job_id=self.id,
            success=True,
            data=data,
            status=status,
            messages=self._stringify_many(getattr(job_data, "messages", [])),
            errors=self._stringify_many(getattr(job_data, "errors", [])),
            queue_position=getattr(job_data, "queue_position", None),
            timeline=getattr(job_data, "timeline", []),
            calibration_set_id=(
                getattr(compilation, "calibration_set_id", None) if compilation else None
            ),
        )

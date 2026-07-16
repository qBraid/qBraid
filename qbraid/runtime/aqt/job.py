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

"""
Module defining AQT job class.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from aqt_connector.models.arnica.response_bodies.jobs import ResultResponse, RRFinished

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData, MeasCount

if TYPE_CHECKING:
    from aqt_connector.models.arnica.jobs import BasicJobMetadata

    import qbraid.runtime.aqt.provider

# Maps the arnica ``JobStatus`` enum values to qBraid ``JobStatus``.
_STATUS_MAP = {
    "queued": JobStatus.QUEUED,
    "ongoing": JobStatus.RUNNING,
    "finished": JobStatus.COMPLETED,
    "error": JobStatus.FAILED,
    "cancelled": JobStatus.CANCELLED,
}


class AQTJobError(QbraidRuntimeError):
    """Class for errors raised while processing an AQT job."""


def _samples_to_counts(
    result: dict[int, list[list[int]]],
) -> Union[MeasCount, list[MeasCount]]:
    """Convert AQT per-shot measurement samples to bitstring counts.

    The arnica finished result maps each circuit index to a list of shots, where each shot is a
    list of per-qubit measurement outcomes ordered ``[q0, q1, ...]``, e.g.
    ``{0: [[1, 0], [1, 1], ...]}``. Each sample is reversed so the bitstring follows qBraid's
    little-endian convention (qubit 0 as the least-significant / rightmost bit), matching the AWS
    result builder.
    """
    per_circuit: list[MeasCount] = []
    for index in sorted(result, key=int):
        counts: MeasCount = {}
        for sample in result[index]:
            bitstring = "".join(str(bit) for bit in reversed(sample))
            counts[bitstring] = counts.get(bitstring, 0) + 1
        per_circuit.append(counts)

    if len(per_circuit) == 1:
        return per_circuit[0]
    return per_circuit


class AQTJob(QuantumJob):
    """AQT job class."""

    def __init__(
        self,
        job_id: str,
        session: Optional[qbraid.runtime.aqt.provider.AQTSession] = None,
        **kwargs,
    ):
        super().__init__(job_id=job_id, **kwargs)
        if session is None:
            # pylint: disable-next=import-outside-toplevel
            from qbraid.runtime.aqt.provider import AQTSession

            session = AQTSession()
        self._session = session

    @property
    def session(self) -> qbraid.runtime.aqt.provider.AQTSession:
        """Return the AQT session."""
        return self._session

    def _fetch_result(self, include_timing_data: bool = False) -> ResultResponse:
        """Fetch and validate ``GET /result/{job_id}`` against the arnica response model.

        The AQT arnica API exposes no dedicated job-status endpoint: ``GET /result/{job_id}`` is
        the canonical job-state endpoint and returns the full result only once the job finished.
        ``include_timing_data`` requests the per-status-change timestamps used by
        :meth:`execution_time_s`.
        """
        return ResultResponse.model_validate(
            self.session.get_result(self.id, include_timing_data=include_timing_data)
        )

    def status(self) -> JobStatus:
        """Return the current status of the AQT job."""
        response = self._fetch_result().response
        return _STATUS_MAP.get(response.status.value, JobStatus.UNKNOWN)

    def execution_time_s(self) -> Optional[float]:
        """Return the job's execution time in seconds, or ``None`` if the job hasn't completed.

        Derived from the arnica ``timing_data`` status-change log as the ``ongoing`` -> ``finished``
        span — the time the job spent running, excluding queue wait.

        Raises:
            AQTJobError: If the job has completed but its timing data is unavailable.
        """
        if self.status() != JobStatus.COMPLETED:
            return None

        response = self._fetch_result(include_timing_data=True).response
        timestamps = {
            change.new_status.value: change.timestamp for change in (response.timing_data or [])
        }
        ongoing = timestamps.get("ongoing")
        finished = timestamps.get("finished")
        if ongoing is None or finished is None:
            raise AQTJobError(
                f"Execution time not available for {self.id}: timing data is incomplete."
            )
        return (finished - ongoing).total_seconds()

    def cancel(self) -> None:
        """Cancel the AQT job."""
        self.session.cancel_job(self.id)

    def _device_id(self, job: BasicJobMetadata) -> str:
        """Resolve the device id for the result, from the device or the job metadata."""
        if self._device is not None:
            return self._device.id
        return f"{job.workspace_id}/{job.resource_id}"

    def result(self) -> Result:
        """Wait for the AQT job to finish and return its result."""
        self.wait_for_final_state()
        parsed = self._fetch_result()
        response = parsed.response

        if not isinstance(response, RRFinished):
            message = getattr(response, "message", "")
            raise AQTJobError(
                f"Job {self.id} did not finish successfully "
                f"(status={response.status.value}). {message}".strip()
            )

        measurement_counts = _samples_to_counts(response.result)
        data = GateModelResultData(measurement_counts=measurement_counts)
        return Result(
            device_id=self._device_id(parsed.job),
            job_id=self.id,
            success=True,
            data=data,
        )

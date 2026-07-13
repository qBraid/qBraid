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

from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData, MeasCount

if TYPE_CHECKING:
    import qbraid.runtime.aqt.provider

_STATUS_MAP = {
    "queued": JobStatus.QUEUED,
    "ongoing": JobStatus.RUNNING,
    "finished": JobStatus.COMPLETED,
    "error": JobStatus.FAILED,
    "cancelled": JobStatus.CANCELLED,
}


class AQTJobError(QbraidRuntimeError):
    """Class for errors raised while processing an AQT job."""


def _samples_to_counts(result: dict[str, Any]) -> Union[MeasCount, list[MeasCount]]:
    """Convert AQT per-shot measurement samples to bitstring counts.

    The arnica result maps each circuit index to a list of shots, where each shot is a list of
    per-qubit measurement outcomes, e.g. ``{"0": [[1, 0], [1, 1], ...]}``.
    """
    per_circuit: list[MeasCount] = []
    for index in sorted(result, key=int):
        counts: MeasCount = {}
        for sample in result[index]:
            bitstring = "".join(str(bit) for bit in sample)
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

    @staticmethod
    def _map_status(status: Optional[str]) -> JobStatus:
        """Convert an AQT job status to a qBraid ``JobStatus``."""
        return _STATUS_MAP.get(status, JobStatus.UNKNOWN)

    def status(self) -> JobStatus:
        """Return the current status of the AQT job.

        The AQT arnica API exposes no dedicated job-status endpoint: ``GET /result/{job_id}`` is
        the canonical job-state endpoint (its ``response.status`` is one of
        ``queued`` / ``ongoing`` / ``finished`` / ``error`` / ``cancelled``) and returns the full
        result only once the job has finished. This is the same endpoint the official
        ``aqt_connector.fetch_job_state`` helper polls. It is called here without timing data, so
        the response stays lightweight while the job is still queued or ongoing.
        """
        response = self.session.get_result(self.id).get("response", {})
        return self._map_status(response.get("status"))

    def cancel(self) -> None:
        """Cancel the AQT job."""
        self.session.cancel_job(self.id)

    def _device_id(self, job_metadata: dict[str, Any]) -> str:
        """Resolve the device id for the result, from the device or the job metadata."""
        if self._device is not None:
            return self._device.id
        workspace_id = job_metadata.get("workspace_id", "")
        resource_id = job_metadata.get("resource_id", "")
        return f"{workspace_id}/{resource_id}"

    def result(self) -> Result:
        """Wait for the AQT job to finish and return its result."""
        self.wait_for_final_state()
        payload = self.session.get_result(self.id)
        response = payload.get("response", {})
        status = response.get("status")

        if status != "finished":
            message = response.get("message", "")
            raise AQTJobError(
                f"Job {self.id} did not finish successfully (status={status}). {message}".strip()
            )

        measurement_counts = _samples_to_counts(response.get("result", {}))
        data = GateModelResultData(measurement_counts=measurement_counts)
        return Result(
            device_id=self._device_id(payload.get("job", {})),
            job_id=self.id,
            success=True,
            data=data,
        )

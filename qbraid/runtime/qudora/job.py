# Copyright 2025 qBraid
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
Module defining QUDORA job class

"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Union

from qbraid_core._import import LazyLoader

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData, MeasCount

if TYPE_CHECKING:
    import qbraid.runtime.qudora

qbraid_rt_qudora = LazyLoader("qbraid_rt_qudora", globals(), "qbraid.runtime.qudora")

# Fields excluded when forwarding the raw QUDORA job record into ``Result`` details.
_RESULT_RESERVED = {"result", "device_id", "job_id", "success", "data"}


class QudoraJobError(QbraidRuntimeError):
    """Class for errors raised while processing a QUDORA job."""


class QudoraJob(QuantumJob):
    """QUDORA job class."""

    def __init__(
        self, job_id: str, session: Optional[qbraid.runtime.qudora.QudoraSession] = None, **kwargs
    ):
        super().__init__(job_id=job_id, **kwargs)
        self._session = session or qbraid_rt_qudora.QudoraSession()

    @property
    def session(self) -> qbraid.runtime.qudora.QudoraSession:
        """Return the QUDORA session."""
        return self._session

    @staticmethod
    def _map_status(status: Optional[str]) -> JobStatus:
        """Convert a QUDORA ``JobStatusName`` to a qBraid ``JobStatus``."""
        status_map = {
            "Submitted": JobStatus.QUEUED,
            "Queuing": JobStatus.QUEUED,
            "Uncompiled": JobStatus.QUEUED,
            "Reserved": JobStatus.QUEUED,
            "Running": JobStatus.RUNNING,
            "Cancelling": JobStatus.CANCELLING,
            "Completed": JobStatus.COMPLETED,
            "Canceled": JobStatus.CANCELLED,
            "Deleted": JobStatus.CANCELLED,
            "Failed": JobStatus.FAILED,
        }
        return status_map.get(status, JobStatus.UNKNOWN)

    def status(self) -> JobStatus:
        """Return the current status of the QUDORA job."""
        job_data = self.session.get_job(self.id)
        return self._map_status(job_data.get("status"))

    def cancel(self) -> None:
        """Cancel the QUDORA job."""
        self.session.cancel_job(self.id)

    @staticmethod
    def _parse_counts(result: list[str]) -> Union[MeasCount, list[MeasCount]]:
        """Parse the QUDORA ``result`` field (a list of JSON count-dict strings).

        Each element is the measurement histogram of one program. The bitstring key
        orientation is preserved exactly as returned by the QUDORA API (matching the
        vendor ``qudora-sdk``, which forwards the same dict to Qiskit unchanged).
        """
        counts: list[MeasCount] = [json.loads(entry) for entry in result]
        return counts[0] if len(counts) == 1 else counts

    def result(self) -> Result:
        """Return the result of the QUDORA job."""
        self.wait_for_final_state()
        job_data = self.session.get_job(self.id, include_results=True)
        status = self._map_status(job_data.get("status"))
        success = status == JobStatus.COMPLETED

        if not success:
            message = job_data.get("user_error") or f"job ended with status {status.name}"
            raise QudoraJobError(f"QUDORA job {self.id} did not complete: {message}.")

        result_payload = job_data.get("result")
        if not result_payload:
            raise QudoraJobError(f"QUDORA job {self.id} completed but returned no result data.")

        data = GateModelResultData(measurement_counts=self._parse_counts(result_payload))
        device_id = job_data.get("target") or (
            self._device.id if self._device is not None else None
        )
        details = {key: value for key, value in job_data.items() if key not in _RESULT_RESERVED}
        return Result(device_id=device_id, job_id=self.id, success=success, data=data, **details)

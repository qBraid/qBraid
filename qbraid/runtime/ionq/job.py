# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint:disable=invalid-name

"""
Module defining IonQ job class

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid_core._import import LazyLoader

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.postprocess import distribute_counts, normalize_data
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData, MeasCount, MeasProb

if TYPE_CHECKING:
    import qbraid.runtime.ionq

qbraid_rt_ionq: qbraid.runtime.ionq = LazyLoader("qbraid_rt_ionq", globals(), "qbraid.runtime.ionq")


class IonQJobError(QbraidRuntimeError):
    """Class for errors raised while processing an IonQ job."""


class IonQJob(QuantumJob):
    """IonQ job class."""

    def __init__(
        self, job_id: str, session: Optional[qbraid.runtime.ionq.IonQSession] = None, **kwargs
    ):
        super().__init__(job_id=job_id, **kwargs)
        self._session = session or qbraid_rt_ionq.IonQSession()

    @property
    def session(self) -> qbraid.runtime.ionq.IonQSession:
        """Return the IonQ session."""
        return self._session

    @staticmethod
    def _map_status(status: str) -> JobStatus:
        """Convert IonQ job status to qBraid job status."""
        status_map = {
            "submitted": JobStatus.INITIALIZING,
            "ready": JobStatus.QUEUED,
            "running": JobStatus.RUNNING,
            "failed": JobStatus.FAILED,
            "canceled": JobStatus.CANCELLED,
            "completed": JobStatus.COMPLETED,
        }
        return status_map.get(status, JobStatus.UNKNOWN)

    def status(self) -> JobStatus:
        """Return the current status of the IonQ job."""
        job_data = self.session.get_job(self.id)
        status = job_data.get("status")
        return self._map_status(status)

    def metadata(self) -> dict[str, Any]:
        """Store and return the metadata of the IonQ job."""
        if self.is_terminal_state() and "status" in self._cache_metadata:
            return self._cache_metadata

        job_metadata = self.session.get_job(self.id)
        self._cache_metadata.update(job_metadata)
        self._cache_metadata["status"] = self._map_status(self._cache_metadata["status"])
        return self._cache_metadata

    def cancel(self) -> None:
        """Cancel the IonQ job."""
        self.session.cancel_job(self.id)

    @staticmethod
    def _get_counts(result: dict[str, Any]) -> Union[MeasCount, list[MeasCount]]:
        """Return the raw counts of the run."""
        shots: Optional[int] = result.get("shots")
        probabilities: Optional[Union[MeasProb, dict[str, MeasProb]]] = result.get("probabilities")

        if shots is None or probabilities is None:
            raise ValueError("Missing shots or probabilities in result data.")

        def convert_to_counts(meas_prob: dict[str, float]) -> dict[str, int]:
            """Helper function to normalize probabilities and convert to counts."""
            probs_dec = {int(key): value for key, value in meas_prob.items()}
            probs_normal = normalize_data(probs_dec)
            return distribute_counts(probs_normal, shots)

        if all(isinstance(value, dict) for value in probabilities.values()):
            return [convert_to_counts(probs) for probs in probabilities.values()]

        return convert_to_counts(probabilities)

    def result(self) -> Result:
        """Return the result of the IonQ job."""
        self.wait_for_final_state()
        job_data = self.session.get_job(self.id)
        success = job_data.get("status") == "completed"
        if not success:
            failure: dict = job_data.get("failure", {})
            code = failure.get("code")
            message = failure.get("error")
            raise IonQJobError(f"Job failed with code {code}: {message}")

        results_url: str = job_data["results_url"]
        results_endpoint = results_url.split("v0.3")[-1]
        job_data["probabilities"] = self.session.get(results_endpoint).json()
        job_data["shots"] = job_data.get("shots", self._cache_metadata.get("shots"))

        measurement_counts = self._get_counts(job_data)
        data = GateModelResultData(measurement_counts=measurement_counts)
        return Result(
            device_id=job_data["target"], job_id=self.id, success=success, data=data, **job_data
        )

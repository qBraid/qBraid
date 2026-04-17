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

# pylint:disable=invalid-name

"""
Module defining IonQ job class

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, TypedDict, Union

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


class CostValue(TypedDict):
    """Type for cost/estimated_cost values."""

    value: float
    unit: str


class IonQJobCost(TypedDict):
    """Type for IonQ job cost response."""

    dry_run: bool
    estimated_cost: CostValue
    cost: Optional[CostValue]


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
            "started": JobStatus.RUNNING,
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

    def cost(self) -> IonQJobCost:
        """Return the cost information for the IonQ job."""
        return self.session.get(f"/jobs/{self.id}/cost").json()

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

    @staticmethod
    def _transform_measurement_probabilities(
        probabilities: Union[MeasProb, dict[str, MeasProb]],
    ) -> Union[MeasProb, list[MeasProb]]:
        """Normalize raw probabilities from decimal integer keys to bit-string keys."""

        def normalize(meas_prob: dict) -> dict[str, float]:
            probs_dec = {int(key): value for key, value in meas_prob.items()}
            return normalize_data(probs_dec)

        if all(isinstance(value, dict) for value in probabilities.values()):
            return [normalize(probs) for probs in probabilities.values()]

        return normalize(probabilities)

    def result(self) -> Result:
        """Return the result of the IonQ job."""
        self.wait_for_final_state()
        job_data = self.session.get_job(self.id)
        success = job_data.get("status") == "completed"
        if not success:
            failure: dict = job_data.get("failure") or {}
            code = failure.get("code")
            message = failure.get("error")
            raise IonQJobError(f"Job failed with code {code}: {message}")

        is_multi_circuit = job_data.get("type") == "ionq.multi-circuit.v1"
        probs_endpoint = (
            f"/jobs/{self.id}/results/probabilities/aggregated"
            if is_multi_circuit
            else f"/jobs/{self.id}/results/probabilities"
        )
        raw_probs = self.session.get(probs_endpoint).json()
        job_data["probabilities"] = raw_probs
        job_data["results"] = {"probabilities": raw_probs}
        job_data["shots"] = job_data.get("shots", self._cache_metadata.get("shots"))

        measurement_counts = self._get_counts(job_data)
        measurement_probabilities = self._transform_measurement_probabilities(
            job_data["probabilities"]
        )
        data = GateModelResultData(
            measurement_counts=measurement_counts,
            measurement_probabilities=measurement_probabilities,
        )
        return Result(
            device_id=job_data["backend"], job_id=self.id, success=success, data=data, **job_data
        )

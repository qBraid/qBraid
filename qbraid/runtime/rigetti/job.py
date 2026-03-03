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
Module defining Rigetti job class

"""

import warnings
from typing import TYPE_CHECKING, Any

from qcs_sdk.qpu.api import QpuApiError, cancel_job, retrieve_results

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    from .device import RigettiDevice


class RigettiJobError(QbraidRuntimeError):
    """Class for errors raised while processing an Rigetti job."""


class RigettiJob(QuantumJob):
    """Rigetti job class."""

    def __init__(
        self,
        job_id: str | int,
        device: "RigettiDevice",
        num_shots: int = 1,
        **kwargs: Any,
    ):
        super().__init__(job_id=job_id, **kwargs)
        self._device = device
        self._num_shots = num_shots
        self._status = JobStatus.RUNNING

    @property
    def _quantum_processor_id(self) -> str:
        return self._device.profile.device_id

    @property
    def _client(self):
        return self._device._qcs_client

    def status(self) -> JobStatus:
        """Return the current status of the Rigetti job."""
        return self._status

    def cancel(self) -> None:
        """Cancel the Rigetti job."""
        try:
            self._status = JobStatus.CANCELLING
            cancel_job(
                job_id=self._job_id,
                quantum_processor_id=self._quantum_processor_id,
                client=self._client,
            )
        except QpuApiError:
            warnings.warn(
                UserWarning(
                    "Failed to cancel the QPU job. "
                    "Cancellation is not guaranteed, as it "
                    "is based on job state at the time of cancellation."
                )
            )
            self._status = JobStatus.RUNNING
        else:
            self._status = JobStatus.CANCELLED

    def get_result(self) -> dict[str, Any]:
        """
        Retrieve and translate Rigetti's readout data into a format
        that can be consumed by qBraid runtime.
        """
        execution_results = retrieve_results(
            job_id=self._job_id,
            quantum_processor_id=self._quantum_processor_id,
            client=self._client,
        )

        ro_memory = execution_results.memory.get("ro")
        if ro_memory is None:
            raise RigettiJobError("No 'ro' register found in execution results.")

        flat = ro_memory.to_binary()
        num_qubits = len(flat) // self._num_shots

        measurements = []
        for i in range(self._num_shots):
            row = flat[i * num_qubits : (i + 1) * num_qubits]
            measurements.append("".join(str(b) for b in row))

        counts = {m: measurements.count(m) for m in set(measurements)}
        total_counts = sum(counts.values())
        probabilities = {outcome: count / total_counts for outcome, count in counts.items()}
        return {"counts": counts, "probabilities": probabilities}

    def result(self) -> Result:
        """Return the result of the Rigetti job."""
        try:
            result = self.get_result()
        except (QpuApiError, RigettiJobError):
            self._status = JobStatus.FAILED
            return Result(
                device_id=self._device.profile.device_id,
                job_id=self._job_id,
                success=False,
                data=None,
            )
        self._status = JobStatus.COMPLETED

        return Result(
            device_id=self._device.profile.device_id,
            job_id=self._job_id,
            success=True,
            data=GateModelResultData(
                measurement_counts=result["counts"],
                measurement_probabilities=result["probabilities"],
            ),
        )

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

# pylint: disable=no-name-in-module

# The above disable is necessary because the qcs_sdk.* modules load from Rust extension bindings
# (__file__ is None for submodules), so pylint/astroid can’t reliably introspect exported names
# and emits E0611 false positives.
#
"""
Module defining Rigetti job class

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from qcs_sdk.qpu.api import ExecutionOptions, QpuApiError, cancel_job, retrieve_results

from qbraid.runtime import JobStateError
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .device import RigettiDevice


class RigettiJobError(QbraidRuntimeError):
    """Class for errors raised while processing an Rigetti job."""


class RigettiJob(QuantumJob):
    """Rigetti job class."""

    def __init__(
        self,
        job_id: str | int,
        device: RigettiDevice,
        num_shots: int = 1,
        **kwargs: Any,
    ):
        super().__init__(job_id=job_id, device=device, **kwargs)
        self._num_shots = num_shots
        self._status = JobStatus.INITIALIZING
        self._cached_results = None

    @property
    def _client(self):
        return self._device._qcs_client

    def status(self) -> JobStatus:
        """Return the current status of the Rigetti job.

        The QCS SDK does not expose a job-status endpoint. Instead,
        ``retrieve_results`` blocks until the job completes. This method
        attempts a retrieval to detect completion or failure and caches
        the result for later use by ``get_result()``.
        """
        if self._status in JobStatus.terminal_states():
            return self._status

        try:
            # TODO: Figure out what status enums are returned in the
            # qcs_sdk when we query the details of the job, and
            # map those to the JobStatus enums.
            # Currently, there is no way to know if the job is queued,
            # or running, or in some other non-terminal state
            self._cached_results = retrieve_results(
                job_id=str(self.id),
                quantum_processor_id=self._device.id,
                client=self._client,
                execution_options=ExecutionOptions.default(),
            )
            self._status = JobStatus.COMPLETED
        except QpuApiError as err:
            if "timeout" in str(err).lower():
                logger.info("Retrieve timed out for job %s; job may still be running.", self.id)
            else:
                self._status = JobStatus.FAILED

        return self._status

    def cancel(self) -> None:
        """Cancel the Rigetti job.
        We set the job status internally in the cancel job because
        the QCS API does not return status updates for job cancellation.
        """
        if self._status in JobStatus.terminal_states():
            raise JobStateError(f"Cannot cancel job {self.id} in terminal state {self._status}.")
        previous_status = self._status
        self._status = JobStatus.CANCELLING
        try:
            logger.info(
                "Attempting to cancel Rigetti job %s on device %s",
                self.id,
                self._device.id,
            )
            cancel_job(
                job_id=str(self.id),
                quantum_processor_id=self._device.id,
                client=self._client,
            )
        except QpuApiError as exc:
            self._status = previous_status
            raise RigettiJobError(
                "Failed to cancel the QPU job. "
                "Cancellation is not guaranteed, as it "
                "is based on job state at the time of cancellation."
            ) from exc
        self._status = JobStatus.CANCELLED
        logger.info(
            "Successfully cancelled Rigetti job %s on device %s",
            self.id,
            self._device.id,
        )

    def _parse_results(self, execution_results) -> GateModelResultData:
        """Parse raw execution results into GateModelResultData.

        Extracts the 'ro' readout register, reshapes the flat binary
        list into per-shot measurement strings, and builds counts.
        """
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
        return GateModelResultData(measurement_counts=counts)

    def result(self, timeout: Optional[int] = None) -> Result:
        """Return the result of the Rigetti job.

        Raises:
            RigettiJobError: If the job result cannot be retrieved or parsed.
        """
        self.wait_for_final_state(timeout=timeout)
        if self._cached_results is None:
            self._cached_results = retrieve_results(
                job_id=str(self.id),
                quantum_processor_id=self._device.id,
                client=self._client,
                execution_options=ExecutionOptions.default(),
            )
        result_data = self._parse_results(self._cached_results)

        self._status = JobStatus.COMPLETED
        return Result[GateModelResultData](
            device_id=self._device.id,
            job_id=self.id,
            success=True,
            data=result_data,
        )

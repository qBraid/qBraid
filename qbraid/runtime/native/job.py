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
Module defining QbraidJob class

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from qbraid_core.services.runtime import QuantumRuntimeClient

from qbraid._logging import logger
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError, QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result, ResultDataType
from qbraid.runtime.result_data import ResultData

if TYPE_CHECKING:
    import qbraid_core.services.runtime

    import qbraid.runtime


class QbraidJob(QuantumJob):
    """Class representing a qBraid job."""

    def __init__(
        self,
        job_id: str,
        device: Optional[qbraid.runtime.QbraidDevice] = None,
        client: Optional[qbraid_core.services.runtime.QuantumRuntimeClient] = None,
        **kwargs,
    ):
        super().__init__(job_id, device, **kwargs)
        self._device = device
        self._client = client

    @property
    def client(self) -> qbraid_core.services.runtime.QuantumRuntimeClient:
        """
        Lazily initializes and returns the client object associated with the job.
        If the job has an associated device with a client, that client is used.
        Otherwise, a new instance of QuantumClient is created and used.

        Returns:
            QuantumClient: The client object associated with the job.
        """
        if self._client is None:
            self._client = self._device.client if self._device else QuantumRuntimeClient()
        return self._client

    def queue_position(self) -> Optional[int]:
        """Return the position of the job in the queue."""
        return self.metadata()["queuePosition"]

    def status(self) -> JobStatus:
        """Return the status of the job / task , among the values of ``JobStatus``."""
        terminal_states = JobStatus.terminal_states()
        if self._cache_metadata.get("status") not in terminal_states:
            job_model = self.client.get_job(self.id)
            status = job_model.status
            job_data = job_model.model_dump(exclude={"statusMsg"})
            if job_model.statusMsg is not None:
                status.set_status_message(job_model.statusMsg)
            self._cache_metadata.update({**job_data, "status": status})
        return self._cache_metadata["status"]

    def metadata(self) -> dict[str, Any]:
        """Return the metadata regarding the job."""
        self._cache_metadata.pop("job_id", None)
        if self._cache_metadata.get("program") is None:
            self._cache_metadata["program"] = self.client.get_job_program(self.id)
        return super().metadata()

    def cancel(self) -> None:
        """Attempt to cancel the job."""
        if self.is_terminal_state():
            raise JobStateError("Cannot cancel job in a terminal state.")

        self.client.cancel_job(self.id)
        logger.info("Cancel job request validated.")

        try:
            logger.info("Waiting for job to cancel...")
            self.wait_for_final_state(timeout=3, poll_interval=1)
        except TimeoutError:
            pass

        status = self.status()
        if status not in {JobStatus.CANCELLED, JobStatus.CANCELLING}:
            raise QbraidRuntimeError(f"Failed to cancel job. Current status: {status.name}")

        logger.info("Success. Current status: %s", status.name)

    def result(self, timeout: Optional[int] = None) -> Result[ResultDataType]:
        """Return the results of the job."""
        self.wait_for_final_state(timeout=timeout)
        job_data = self.client.get_job(self.id)
        cost = job_data.cost
        time_stamps = job_data.timeStamps
        success = job_data.status == JobStatus.COMPLETED
        job_result = self.client.get_job_result(self.id) if success else None
        data = ResultData.from_object(job_result, job_data.experimentType)
        return Result[ResultDataType](
            device_id=job_data.deviceQrn,
            job_id=job_data.jobQrn,
            success=success,
            data=data,
            time_stamps=time_stamps,
            cost=cost,
        )

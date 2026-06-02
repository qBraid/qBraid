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
Module defining OpenQuantum job class

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from qbraid_core._import import LazyLoader

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    import qbraid.runtime.openquantum

qbraid_rt_oq = LazyLoader("qbraid_rt_oq", globals(), "qbraid.runtime.openquantum")

# Execution plan and queue priority mappings
EXECUTION_PLAN_TYPES = {
    "PUBLIC": "072f7eb6-574b-4bae-aafa-d3399c4abe7a",
    "PRIVATE": "f83fd52f-c691-470f-9521-26b81c4e53bd",
}

QUEUE_PRIORITY_TYPES = {
    "STANDARD": "0f7b91a3-d1bf-46fb-af9c-55b77fa72bed",
    "PRIORITY": "4ea2b9de-2d20-46d4-b1b5-0b71537a584f",
    "INSTANT": "74cebc3d-14d8-455d-900e-daedc1566384",
}


class OpenQuantumJob(QuantumJob):
    """OpenQuantum job class."""

    def __init__(
        self,
        job_id: str,
        session: Optional[qbraid.runtime.openquantum.OpenQuantumSession] = None,
        device: Optional[qbraid.runtime.QuantumDevice] = None,
        **kwargs,
    ):
        super().__init__(job_id, device=device, **kwargs)
        self._session = session or qbraid_rt_oq.OpenQuantumSession()

    @property
    def session(self) -> qbraid.runtime.openquantum.OpenQuantumSession:
        """Return the OpenQuantum session."""
        return self._session

    def status(self) -> JobStatus:
        """Return the current status of the OpenQuantum job."""
        job_data = self.session.get_job(self.id)
        status = job_data.get("status", "")

        if status in ["Created", "Pending"]:
            return JobStatus.INITIALIZING
        if status == "Queued":
            return JobStatus.QUEUED
        if status == "Running":
            return JobStatus.RUNNING
        if status == "Completed":
            return JobStatus.COMPLETED
        if status == "Failed":
            return JobStatus.FAILED
        if status == "Canceled":
            return JobStatus.CANCELLED

        return JobStatus.UNKNOWN

    def cancel(self) -> None:
        """Cancel the OpenQuantum job."""
        self.session.cancel_job(self.id)

    def result(self) -> Result:
        """Return the result of the OpenQuantum job."""
        self.wait_for_final_state()
        job_data = self.session.get_job(self.id)
        if job_data.get("status", "") != "Completed":
            raise QbraidRuntimeError(f"Job failed: {job_data.get('message')}")

        results = self.session.download_job_output(self.id)
        data = GateModelResultData(measurement_counts=results)
        device_id = self._device.id if self._device else job_data.get("backend_class_id", "")

        # Add readable execution plan and queue priority names
        enhanced_job_data = dict(job_data)
        execution_plan_id = job_data.get("execution_plan_id")
        queue_priority_id = job_data.get("queue_priority_id")

        # Create reverse mappings
        execution_plan_reverse = {v: k for k, v in EXECUTION_PLAN_TYPES.items()}
        queue_priority_reverse = {v: k for k, v in QUEUE_PRIORITY_TYPES.items()}

        if execution_plan_id and execution_plan_id in execution_plan_reverse:
            enhanced_job_data["execution_plan"] = execution_plan_reverse[execution_plan_id]

        if queue_priority_id and queue_priority_id in queue_priority_reverse:
            enhanced_job_data["queue_priority"] = queue_priority_reverse[queue_priority_id]

        return Result(
            device_id=device_id, job_id=self.id, success=True, data=data, **enhanced_job_data
        )

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
Module defining the QDI job class

"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

from .exceptions import QdiJobError, qdi_call
from .protocol import QdiTaskStatus

if TYPE_CHECKING:
    import qbraid.runtime.qdi
    from qbraid.runtime.qdi.protocol import QdiClient

# Maps the five QDI task states (spec §3.3) onto qBraid ``JobStatus``.
_TASK_STATUS_MAP: dict[QdiTaskStatus, JobStatus] = {
    QdiTaskStatus.QUEUED: JobStatus.QUEUED,
    QdiTaskStatus.EXECUTING: JobStatus.RUNNING,
    QdiTaskStatus.COMPLETED: JobStatus.COMPLETED,
    QdiTaskStatus.FAULTED: JobStatus.FAILED,
    QdiTaskStatus.CANCELLED: JobStatus.CANCELLED,
}

# The only ``result_type`` the working-group implementations emit so far.
COUNTS_RESULT_TYPE = "counts"


class QdiJob(QuantumJob):
    """Job class for a task submitted through QDI."""

    def __init__(
        self,
        job_id: str,
        client: QdiClient | None = None,
        device: qbraid.runtime.qdi.QdiDevice | None = None,
        device_id: str | None = None,
        **kwargs,
    ):
        """Create a job handle for a QDI task.

        QDI Monitor and Receive both target a ``device_id`` as well as a task
        id, so one must be given either directly or via ``device``. A job
        rehydrated with ``load_job(task_id, "qdi", client=..., device_id=...)``
        takes the direct form.
        """
        if client is None and device is not None:
            client = device.client
        if client is None:
            raise ValueError("QdiJob requires a QDI client, either directly or via device.")
        if device_id is None and device is not None:
            device_id = device.id
        if device_id is None:
            raise ValueError("QdiJob requires a device_id, either directly or via device.")
        super().__init__(job_id=job_id, device=device, device_id=device_id, **kwargs)
        self._client = client
        self._device_id = device_id

    @property
    def client(self) -> QdiClient:
        """Return the QDI client this job polls through."""
        return self._client

    @property
    def device_id(self) -> str:
        """Return the ``device_id`` the task was sent to."""
        return self._device_id

    def _monitor(self) -> tuple[JobStatus, dict[str, Any]]:
        with qdi_call("monitor"):
            raw_status, advisory = self._client.monitor(self._device_id, str(self.id))
        try:
            task_status = QdiTaskStatus(raw_status)
        except ValueError as err:
            # Defaulting to UNKNOWN would leave result() polling a finished
            # task until wait_for_final_state times out.
            raise QdiJobError(
                f"QDI client reported task status {raw_status!r}, which is not one of "
                f"{[status.name for status in QdiTaskStatus]}."
            ) from err
        self._cache_metadata["advisory"] = advisory
        return _TASK_STATUS_MAP[task_status], advisory

    def status(self) -> JobStatus:
        """Return the current status of the QDI task."""
        return self._monitor()[0]

    def cancel(self) -> None:
        """Always raises: QDI v0.2 defines a ``CANCELLED`` state but no operation that causes it."""
        raise QdiJobError(
            "QDI v0.2 has no Cancel operation. Cancel the task through the vendor's own "
            "interface if it offers one."
        )

    def result(self) -> Result:
        """Wait for the task to finish and return its measurement counts."""
        self.wait_for_final_state()
        status, advisory = self._monitor()
        if status != JobStatus.COMPLETED:
            raise QdiJobError(
                f"QDI task {self.id} ended with status {status.name}; advisory: {advisory}."
            )

        with qdi_call("receive"):
            payload, result_type = self._client.receive(self._device_id, str(self.id))

        if result_type != COUNTS_RESULT_TYPE:
            raise QdiJobError(
                f"QDI task {self.id} returned result_type '{result_type}'; only "
                f"'{COUNTS_RESULT_TYPE}' is supported."
            )
        counts = json.loads(payload)
        if not isinstance(counts, dict):
            raise QdiJobError(
                f"QDI task {self.id} returned a '{result_type}' payload that is not a histogram."
            )

        data = GateModelResultData(measurement_counts=counts)
        return Result(
            device_id=self._device_id,
            job_id=self.id,
            success=True,
            data=data,
            result_type=result_type,
            advisory=advisory,
            shots=self._cache_metadata.get("shots"),
            task_type=self._cache_metadata.get("task_type"),
        )

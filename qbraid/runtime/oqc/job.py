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

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob

from qcaas_client.client import OQCClient

from .result import OQCJobResult

class OQCJob(QuantumJob):
    """OQC job class."""

    def __init__(self, job_id: str, qpu_id: str, client: OQCClient, **kwargs):
        super().__init__(job_id=job_id)
        self._qpu_id = qpu_id
        self._client = client

    def cancel(self):
        self._client.cancel_task(task_id=self.id, qpu_id=self._qpu_id)

    def result(self):
        return OQCJobResult(job_id=self.id, qpu_id=self._qpu_id, client=self._client)

    def status(self):
        task_status = self._client.get_task_status(task_id=self.id, qpu_id=self._qpu_id)

        status_map = {
            "CREATED": JobStatus.INITIALIZING,
            "SUBMITTED": JobStatus.INITIALIZING,
            "RUNNING": JobStatus.RUNNING,
            "FAILED": JobStatus.FAILED,
            "CANCELLED": JobStatus.CANCELLED,
            "COMPLETED": JobStatus.COMPLETED,
            "UNKNOWN": JobStatus.UNKNOWN,
            "EXPIRED": JobStatus.FAILED
        }

        return status_map.get(task_status, JobStatus.UNKNOWN)

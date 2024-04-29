# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining QiskitJob Class

"""
import logging
from typing import Optional

import qiskit.providers.job
from qiskit_ibm_provider.job.exceptions import IBMJobInvalidStateError

from qbraid.runtime.enums import JOB_FINAL, JobStatus
from qbraid.runtime.exceptions import JobStateError
from qbraid.runtime.job import QuantumJob

from .result import QiskitResult

logger = logging.getLogger(__name__)

IBM_JOB_STATUS_MAP = {
    "JobStatus.INITIALIZING": JobStatus.INITIALIZING,
    "JobStatus.QUEUED": JobStatus.QUEUED,
    "JobStatus.VALIDATING": JobStatus.VALIDATING,
    "JobStatus.RUNNING": JobStatus.RUNNING,
    "JobStatus.CANCELLED": JobStatus.CANCELLED,
    "JobStatus.DONE": JobStatus.COMPLETED,
    "JobStatus.ERROR": JobStatus.FAILED,
}


class QiskitJob(QuantumJob):
    """Wrapper class for IBM Qiskit ``Job`` objects."""

    def __init__(self, job_id: str, job: Optional[qiskit.providers.job.Job], **kwargs):
        """Create a ``QiskitJob`` object."""
        super().__init__(job_id, **kwargs)
        self._job = job or self._get_job()

    def _get_job(self):
        """Return the job like object that is being wrapped."""
        backend = self.device._device
        provider = backend.provider
        return provider.backend.retrieve_job(self.id)

    def status(self):
        """Returns status from Qiskit Job object."""
        job_status = str(self._job.status())
        status = IBM_JOB_STATUS_MAP.get(job_status, JobStatus.UNKNOWN)
        self._cache_metadata["status"] = status
        return status

    def result(self):
        """Return the results of the job."""
        if self.done():
            logger.info("Result will be available when job has reached final state.")
        return QiskitResult(self._job.result())

    def cancel(self):
        """Attempt to cancel the job."""
        if not self.done():
            raise JobStateError(f"Cannot cancel quantum job in non-terminal state.")
        try:
            return self._job.cancel()
        except IBMJobInvalidStateError as err:
            raise JobStateError from err

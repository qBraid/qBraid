# Copyright (C) 2024 qBraid
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
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.exceptions import RuntimeInvalidStateError

from qbraid._logging import logger
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError, QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import GateModelResultData, Result

from .result_builder import QiskitGateModelResultBuilder

if TYPE_CHECKING:
    import qiskit.result
    import qiskit_ibm_runtime


IBM_JOB_STATUS_MAP = {
    "INITIALIZING": JobStatus.INITIALIZING,
    "QUEUED": JobStatus.QUEUED,
    "VALIDATING": JobStatus.VALIDATING,
    "RUNNING": JobStatus.RUNNING,
    "CANCELLED": JobStatus.CANCELLED,
    "DONE": JobStatus.COMPLETED,
    "ERROR": JobStatus.FAILED,
}


class QiskitJob(QuantumJob):
    """Class for interfacing with a Qiskit IBM ``RuntimeJob``."""

    def __init__(
        self,
        job_id: str,
        job: Optional[qiskit_ibm_runtime.RuntimeJob] = None,
        service: Optional[qiskit_ibm_runtime.QiskitRuntimeService] = None,
        **kwargs,
    ):
        """Create a ``QiskitJob`` instance."""
        super().__init__(job_id, **kwargs)
        self._job = job or self._get_job(service=service)

    def _get_job(self, service: Optional[qiskit_ibm_runtime.QiskitRuntimeService] = None):
        """Return the qiskit_ibm_runtime.RuntimeJob associated with instance id attribute.

        Attempts to retrieve a job using a specified or default service. Handles
        service initialization with error management for authentication issues.

        Raises:
            QbraidRuntimeError: If there is an error initializing the service or retrieving the job.
        """
        if service is None:
            if self._device and getattr(self._device, "_service", None):
                service = self._device._service
            else:
                try:
                    service = QiskitRuntimeService()
                except Exception as err:
                    raise QbraidRuntimeError("Failed to initialize the quantum service.") from err

        try:
            return service.job(self.id)
        except Exception as err:
            raise QbraidRuntimeError(f"Error retrieving job {self.id}") from err

    def status(self):
        """Returns status from Qiskit Job object."""
        job_status = self._job.status().name
        status = IBM_JOB_STATUS_MAP.get(job_status, JobStatus.UNKNOWN)
        self._cache_metadata["status"] = status
        return status

    def queue_position(self) -> Optional[int]:
        """Returns the position of the job in the server queue."""
        return self._job.queue_position(refresh=True)

    def result(self):
        """Return the results of the job."""
        if not self.is_terminal_state():
            logger.info("Result will be available when job has reached final state.")

        runner_result: qiskit.result.Result = self._job.result()
        runner_data = runner_result.to_dict()
        job_id = runner_data.pop("job_id", self._job.job_id())
        success = runner_data.pop("success", runner_result.success)

        builder = QiskitGateModelResultBuilder(runner_result)
        measurement_counts = builder.get_counts()
        measurements = builder.measurements()
        data = GateModelResultData(measurement_counts=measurement_counts, measurements=measurements)

        return Result(
            device_id=runner_result.backend_name,
            job_id=job_id,
            success=success,
            data=data,
            **runner_data,
        )

    def cancel(self):
        """Attempt to cancel the job."""
        if self.is_terminal_state():
            raise JobStateError("Cannot cancel quantum job in non-terminal state.")
        try:
            return self._job.cancel()
        except RuntimeInvalidStateError as err:
            raise JobStateError from err

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

import logging
from typing import TYPE_CHECKING, Optional

import numpy as np
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.exceptions import RuntimeInvalidStateError

from qbraid.runtime.enums import ExperimentType, JobStatus
from qbraid.runtime.exceptions import JobStateError, QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import ExperimentalResult, ResultFormatter, RuntimeJobResult

if TYPE_CHECKING:
    import qiskit_ibm_runtime

logger = logging.getLogger(__name__)

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

    def _build_runtime_gate_model_results(self, job_data, **kwargs):
        # get the counts from qiskit job
        counts = job_data.get_counts()

        def _format_measurements(memory_list):
            """Format the qiskit measurements into int for the given memory list"""
            formatted_meas = []
            for str_shot in memory_list:
                lst_shot = [int(x) for x in list(str_shot)]
                formatted_meas.append(lst_shot)
            return formatted_meas

        # get the measurement data
        num_circuits = len(job_data.results)
        qiskit_meas = [job_data.get_memory(i) for i in range(num_circuits)]
        qbraid_meas = [
            _format_measurements(memory_list=qiskit_meas[i]) for i in range(num_circuits)
        ]
        if num_circuits == 1:
            qbraid_meas = np.array(qbraid_meas[0])
        else:
            qbraid_meas = ResultFormatter.normalize_tuples(qbraid_meas)

        return [
            ExperimentalResult(
                state_counts=counts,
                measurements=qbraid_meas,
                result_type=ExperimentType.GATE_MODEL,
                metadata=None,
            )
        ]

    def result(self):
        """Return the results of the job."""
        if not self.is_terminal_state():
            logger.info("Result will be available when job has reached final state.")

        device_id = self._device.id if self._device else None

        qiskit_job_result = self._job.result()
        exp_results = self.build_runtime_result(ExperimentType.GATE_MODEL, qiskit_job_result)

        return RuntimeJobResult(
            job_id=self.id,
            device_id=device_id,
            results=exp_results,
            success=qiskit_job_result.success,
        )

    def cancel(self):
        """Attempt to cancel the job."""
        if self.is_terminal_state():
            raise JobStateError("Cannot cancel quantum job in non-terminal state.")
        try:
            return self._job.cancel()
        except RuntimeInvalidStateError as err:
            raise JobStateError from err

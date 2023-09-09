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

from qiskit_ibm_provider import IBMBackend
from qiskit_ibm_provider.job.exceptions import IBMJobInvalidStateError

from qbraid.providers.enums import JOB_FINAL
from qbraid.providers.exceptions import JobError, JobStateError
from qbraid.providers.job import QuantumJob

from .result import QiskitResult


class QiskitJob(QuantumJob):
    """Wrapper class for IBM Qiskit ``Job`` objects."""

    def __init__(self, job_id: str, **kwargs):
        """Create a ``QiskitJob`` object."""
        super().__init__(job_id, **kwargs)

    def _get_job(self):
        """Return the job like object that is being wrapped."""
        if not isinstance(self.device._device, IBMBackend):
            raise JobError(
                "Cannot retrieve job submitted to unrecognized backend. Expected device of type "
                f"qiskit_ibm_provider.IBMBackend, but instead got {type(self.device._device)}."
            )
        job_id = self.vendor_job_id
        backend = self.device._device
        provider = backend.provider
        return provider.backend.retrieve_job(job_id)

    def _get_status(self):
        """Returns status from Qiskit Job object."""
        return str(self._job.status())

    def result(self):
        """Return the results of the job."""
        if self.status() not in JOB_FINAL:
            logging.info("Result will be available when job has reached final state.")
        return QiskitResult(self._job.result())

    def cancel(self):
        """Attempt to cancel the job."""
        status = self.status()
        if status in JOB_FINAL:
            raise JobStateError(f"Cannot cancel quantum job in the {status} state.")
        try:
            return self._job.cancel()
        except IBMJobInvalidStateError as err:
            raise JobStateError from err

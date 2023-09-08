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
Module defining IBMJobWrapper Class

"""
import logging

from qiskit_ibm_provider import IBMBackend
from qiskit_ibm_provider.job.exceptions import IBMJobInvalidStateError

from qbraid.providers.enums import JOB_FINAL
from qbraid.providers.exceptions import JobError, JobStateError
from qbraid.providers.job import JobLikeWrapper

from .result import IBMResultWrapper


class IBMJobWrapper(JobLikeWrapper):
    """Wrapper class for IBM Qiskit ``Job`` objects."""

    def __init__(self, job_id: str, **kwargs):
        """Create a ``IBMJobWrapper`` object."""
        super().__init__(job_id, **kwargs)

    def _get_vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        if not isinstance(self.device.vendor_dlo, IBMBackend):
            raise JobError(
                f"Retrieving previously submitted job not supported for {self.device.id}."
            )
        job_id = self.vendor_job_id
        backend = self.device.vendor_dlo
        provider = backend.provider
        return provider.backend.retrieve_job(job_id)

    def _get_status(self):
        """Returns status from Qiskit Job object."""
        return str(self.vendor_jlo.status())

    def result(self):
        """Return the results of the job."""
        if self.status() not in JOB_FINAL:
            logging.info("Result will be available when job has reached final state.")
        return IBMResultWrapper(self.vendor_jlo.result())

    def cancel(self):
        """Attempt to cancel the job."""
        status = self.status()
        if status in JOB_FINAL:
            raise JobStateError(f"Cannot cancel quantum job in the {status} state.")
        try:
            return self.vendor_jlo.cancel()
        except IBMJobInvalidStateError as err:
            raise JobStateError from err

# Copyright 2023 qBraid
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
Module defining IBMJobWrapper Class

"""
import logging

from qiskit_ibm_provider import IBMBackend

from qbraid.devices.enums import JOB_FINAL
from qbraid.devices.exceptions import JobError
from qbraid.devices.job import JobLikeWrapper

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
        return self.vendor_jlo.cancel()

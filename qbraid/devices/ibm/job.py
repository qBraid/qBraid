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
Module defining QiskitJobWrapper Class

"""
import logging

from qiskit.providers.exceptions import JobError as QiskitJobError
from qiskit.providers.ibmq import IBMQBackend
from qiskit.providers.ibmq.managed import IBMQJobManager

from qbraid.devices.enums import JOB_FINAL
from qbraid.devices.exceptions import JobError
from qbraid.devices.job import JobLikeWrapper

from .result import QiskitResultWrapper


class QiskitJobWrapper(JobLikeWrapper):
    """Wrapper class for IBM Qiskit ``Job`` objects."""

    def __init__(self, job_id: str, **kwargs):
        """Create a ``QiskitJobWrapper`` object."""
        super().__init__(job_id, **kwargs)

    def _get_vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        if not isinstance(self.device.vendor_dlo, IBMQBackend):
            raise JobError(
                f"Retrieving previously submitted job not supported for {self.device.id}."
            )
        job_manager = IBMQJobManager()
        job_set_id = self.vendor_job_id
        provider = self.device.vendor_dlo.provider()
        job_set = job_manager.retrieve_job_set(job_set_id=job_set_id, provider=provider)
        jobs = job_set.jobs()  # ATM len(jobs) always 1 b/c qbraid run method takes single circuit
        return jobs[0]

    def _get_status(self):
        """Returns status from Qiskit Job object."""
        return str(self.vendor_jlo.status())

    def submit(self):
        """Submit the job to the backend for execution."""
        try:
            return self.vendor_jlo.submit()
        except QiskitJobError as err:
            raise JobError from err

    def result(self):
        """Return the results of the job."""
        if self.status() not in JOB_FINAL:
            logging.info("Result will be available when job has reached final state.")
        return QiskitResultWrapper(self.vendor_jlo.result())

    def cancel(self):
        """Attempt to cancel the job."""
        return self.vendor_jlo.cancel()

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of the source tree https://github.com/Qiskit/qiskit-terra/blob/main/LICENSE.txt
# or at http://www.apache.org/licenses/LICENSE-2.0.
#
# NOTICE: This file has been modified from the original:
# https://github.com/Qiskit/qiskit-terra/blob/main/qiskit/providers/job.py

"""QiskitJobWrapper Class"""

from __future__ import annotations

from typing import Callable, Optional

from qiskit.providers.exceptions import JobError as QiskitJobError
from qiskit.providers.exceptions import JobTimeoutError
from qiskit.providers.job import Job

from qbraid.devices.exceptions import JobError
from qbraid.devices.job import JobLikeWrapper


class QiskitJobWrapper(JobLikeWrapper):
    """Wrapper class for IBM Qiskit ``Job`` objects."""

    def __init__(self, device, circuit, vendor_jlo: Job):
        """Create a ``QiskitJobWrapper`` object.

        Args:
            device: the QiskitBackendWrapper device object associated with this job
            circuit: qbraid wrapped circuit object used in this job
            vendor_jlo (Job): a Qiskit ``Job`` object used to run circuits.

        """
        super().__init__(device, circuit, vendor_jlo)

    def _set_static(self):
        """Return a dictionary that provides key-value mappings for the following keys:
        * vendor_job_id (str): the job ID from the vendor job-like-object.
        * createdAt (datetime.datime): the time the job was created
        * shots (int): the number of repetitions used in the run

        """
        return {
            "vendor_job_id": self.vendor_jlo.job_id(),
            "createdAt": "TO-DO",
            "shots": "TO-DO",
        }

    def status(self):
        """Return the status of the job."""
        return str(self.vendor_jlo.status())

    def ended_at(self):
        """The time when the job ended."""
        return "TO-DO"

    def submit(self):
        """Submit the job to the backend for execution."""
        try:
            return self.vendor_jlo.submit()
        except QiskitJobError as err:
            raise JobError("qBraid JobError raised from {}".format(type(err))) from err

    def result(self):
        """Return the results of the job."""
        return self.vendor_jlo.result()

    def cancel(self):
        """Attempt to cancel the job."""
        return self.vendor_jlo.cancel()

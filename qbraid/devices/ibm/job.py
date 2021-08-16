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

from typing import Callable, Optional, TYPE_CHECKING
from qiskit.providers.exceptions import JobTimeoutError
from qiskit.providers.exceptions import JobError as QiskitJobError

from qbraid.devices.job import JobLikeWrapper
from qbraid.devices.exceptions import JobError

if TYPE_CHECKING:
    from qiskit.providers.job import Job


class QiskitJobWrapper(JobLikeWrapper):
    """Wrapper class for IBM Qiskit ``Job`` objects."""

    def __init__(self, device, vendor_jlo: 'Job'):
        """Create a QiskitJobWrapper.

        Args:
            device (QiskitBackendWrapper): a Qiskit device object
            vendor_jlo (Job): a Qiskit ``Job`` object used to run circuits.

        """
        super().__init__(device, vendor_jlo)
        self.device = device
        self.vendor_jlo = vendor_jlo

    @property
    def job_id(self):
        """Return a unique id identifying the job."""
        return self.vendor_jlo.job_id

    def metadata(self, **kwargs):
        """Return the metadata regarding the job."""
        return self.vendor_jlo.metadata

    def done(self):
        """Return whether the job has successfully run."""
        return self.vendor_jlo.done()

    def running(self):
        """Return whether the job is actively running."""
        return self.vendor_jlo.running()

    def cancelled(self):
        """Return whether the job has been cancelled."""
        return self.vendor_jlo.cancelled()

    def in_final_state(self):
        """Return whether the job is in a final job state such as ``DONE`` or ``ERROR``."""
        return self.vendor_jlo.in_final_state()

    def wait_for_final_state(
        self, timeout: Optional[float] = None, wait: float = 5, callback: Optional[Callable] = None
    ):
        """Poll the job status until it progresses to a final state such as ``DONE`` or ``ERROR``.

        Args:
            timeout: Seconds to wait for the job. If ``None``, wait indefinitely.
            wait: Seconds between queries.
            callback: Callback function invoked after each query.
                The following positional arguments are provided to the callback function:
                * job_id: Job ID
                * job_status: Status of the job from the last query
                * job: This BaseJob instance
                Note: different subclass might provide different arguments to the callback function.

        Raises:
            JobError: If the job does not reach a final state before the specified timeout.

        """
        try:
            self.vendor_jlo.wait_for_final_state(timeout, wait, callback)
        except JobTimeoutError as err:
            raise JobError("qBraid JobError raised from {}".format(type(err))) from err

    def submit(self):
        """Submit the job to the backend for execution."""
        try:
            return self.vendor_jlo.submit()
        except QiskitJobError as err:
            raise JobError("qBraid JobError raised from {}".format(type(err))) from err

    def result(self):
        """Return the results of the job."""
        return self.vendor_jlo.result()

    def status(self):
        """Return the status of the job."""
        return self.vendor_jlo.status()

    def cancel(self):
        """Attempt to cancel the job."""
        return self.vendor_jlo.cancel()

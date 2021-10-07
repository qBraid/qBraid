"""QiskitJobWrapper Class"""

from __future__ import annotations

from qiskit.providers.exceptions import JobError as QiskitJobError
from qiskit.providers.job import JobV1 as Job

from qbraid.devices.exceptions import JobError
from qbraid.devices.job import JobLikeWrapper


class QiskitJobWrapper(JobLikeWrapper):
    """Wrapper class for IBM Qiskit ``Job`` objects."""

    def __init__(self, job_id, vendor_job_id=None, device=None, vendor_jlo=None):
        """Create a ``QiskitJobWrapper`` object.

        """
        super().__init__(job_id, vendor_job_id, device, vendor_jlo)

    @property
    def vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        return Job(self._device.vendor_dlo, self.vendor_job_id)

    def _status(self):
        """Returns status from Qiskit Job object."""
        return str(self.vendor_jlo.status())

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

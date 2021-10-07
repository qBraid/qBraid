"""QiskitJobWrapper Class"""

from qiskit.providers.exceptions import JobError as QiskitJobError
from qiskit.providers.aer.backends import AerSimulator

from qbraid.devices.exceptions import JobError
from qbraid.devices.job import JobLikeWrapper


class QiskitJobWrapper(JobLikeWrapper):
    """Wrapper class for IBM Qiskit ``Job`` objects."""

    def __init__(self, job_id, vendor_job_id=None, device=None, vendor_jlo=None):
        """Create a ``QiskitJobWrapper`` object."""
        super().__init__(job_id, vendor_job_id, device, vendor_jlo)

    def _get_vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        # backend = self.device.vendor_dlo
        # job_id = self.vendor_job_id
        # fn = self.device.vendor_dlo._run
        # qobj = None  # need to find qobj
        # return AerSimulator(backend, job_id, fn, qobj)
        return NotImplementedError

    def _get_status(self):
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

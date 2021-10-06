"""QiskitJobWrapper Class"""

from __future__ import annotations

from qiskit.providers.exceptions import JobError as QiskitJobError
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

    @property
    def vendor_job_id(self) -> str:
        """Return the job ID from the vendor job-like-object."""
        return self.vendor_jlo.job_id()

    @property
    def _shots(self) -> int:
        """Return the number of repetitions used in the run"""
        return self.device.vendor_dlo.options.get("shots")

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

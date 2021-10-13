"""BraketQuantumtaskWrapper Class"""

from asyncio import Task

from braket.aws import AwsQuantumTask

from qbraid.devices.aws import BraketResultWrapper
from qbraid.devices.job import JobLikeWrapper


class BraketQuantumTaskWrapper(JobLikeWrapper):
    """Wrapper class for Amazon Braket ``QuantumTask`` objects."""

    def __init__(self, job_id, vendor_job_id=None, device=None, vendor_jlo=None):
        """Create a BraketQuantumTaskWrapper."""

        super().__init__(job_id, vendor_job_id, device, vendor_jlo)

    def _get_vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        return AwsQuantumTask(self.vendor_job_id)

    def _get_status(self):
        """Returns status from Braket QuantumTask object metadata."""
        return self.vendor_jlo.metadata()["status"]

    def result(self) -> BraketResultWrapper:
        """Return the results of the job."""
        return BraketResultWrapper(self.vendor_jlo.result())

    def async_result(self) -> Task:
        """asyncio.Task: Get the quantum task result asynchronously."""
        # return self.vendor_jlo.async_result()
        raise NotImplementedError

    def cancel(self):
        """Cancel the quantum task."""
        return self.vendor_jlo.cancel()

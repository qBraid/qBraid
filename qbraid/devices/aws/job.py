"""
Module defining BraketQuantumtaskWrapper Class

"""
import logging

from braket.aws import AwsQuantumTask

from qbraid.devices.enums import JOB_FINAL
from qbraid.devices.job import JobLikeWrapper

from .result import BraketResultWrapper


class BraketQuantumTaskWrapper(JobLikeWrapper):
    """Wrapper class for Amazon Braket ``QuantumTask`` objects."""

    def __init__(self, job_id: str, **kwargs):
        """Create a BraketQuantumTaskWrapper."""

        super().__init__(job_id, **kwargs)

    def _get_vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        return AwsQuantumTask(self.vendor_job_id)

    def _get_status(self):
        """Returns status from Braket QuantumTask object metadata."""
        return self.vendor_jlo.metadata()["status"]

    def result(self) -> BraketResultWrapper:
        """Return the results of the job."""
        if self.status() not in JOB_FINAL:
            logging.info("Result will be available when job has reached final state.")
        return BraketResultWrapper(self.vendor_jlo.result())

    def cancel(self) -> None:
        """Cancel the quantum task."""
        return self.vendor_jlo.cancel()

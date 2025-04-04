"""
Defines the BatchQuantumJob class used for grouping and managing multiple
Braket quantum tasks submitted as a batch.

This abstraction allows users to interact with multiple quantum jobs as a
single job-like object, providing consistent access to results, metadata,
status checking, and job cancellation across different quantum providers.
"""

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.job import QuantumJob


class BatchQuantumJob(QuantumJob):
    """A wrapper class for a batch of QuantumJob instances.

    Used to normalize the return type of device.run(batch) across providers.
    Provides a unified interface for checking status, collecting results,
    and managing metadata of the entire batch as one logical job.

    Attributes:
        jobs (list[QuantumJob]): The individual quantum jobs in the batch.
    """
    def __init__(self, jobs: list[QuantumJob]):
        super().__init__(job_id="batch", device=jobs[0].device)
        self._jobs = jobs

    def status(self):
        statuses = [job.status() for job in self._jobs]
        if all(s == JobStatus.COMPLETED for s in statuses):
            return JobStatus.COMPLETED
        if any(s == JobStatus.FAILED for s in statuses):
            return JobStatus.FAILED
        return JobStatus.RUNNING

    def result(self):
        return [job.result() for job in self._jobs]

    def cancel(self):
        for job in self._jobs:
            job.cancel()

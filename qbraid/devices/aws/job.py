"""BraketQuantumtaskWrapper Class"""

from __future__ import annotations

from asyncio import Task
from typing import Union

from braket.aws import AwsQuantumTask
from braket.tasks.annealing_quantum_task_result import AnnealingQuantumTaskResult
from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult

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

    def result(self) -> Union[AnnealingQuantumTaskResult, GateModelQuantumTaskResult]:
        """Return the results of the job."""
        return self.vendor_jlo.result()

    def async_result(self) -> Task:
        """asyncio.Task: Get the quantum task result asynchronously."""
        return self.vendor_jlo.async_result()

    def cancel(self):
        """Cancel the quantum task."""
        return self.vendor_jlo.cancel()

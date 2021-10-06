"""BraketQuantumtaskWrapper Class"""

from __future__ import annotations

from asyncio import Task
from typing import Union

from braket.tasks import QuantumTask
from braket.tasks.annealing_quantum_task_result import AnnealingQuantumTaskResult
from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult

from qbraid.devices.job import JobLikeWrapper
from qbraid.devices.enums import Status


class BraketQuantumTaskWrapper(JobLikeWrapper):
    """Wrapper class for Amazon Braket ``QuantumTask`` objects."""

    def __init__(self, device, circuit, quantum_task: QuantumTask):
        """Create a BraketQuantumTaskWrapper

        Args:
            device: the BraketDeviceWrapper associated with this quantum task i.e. job
            circuit: qbraid wrapped circuit object used in this job
            quantum_task (QuantumTask): a braket ``QuantumTask`` object used to run circuits.

        """
        super().__init__(device, circuit, quantum_task)

    @property
    def vendor_job_id(self) -> str:
        """Return the job ID from the vendor job-like-object."""
        return self.vendor_jlo.metadata()["quantumTaskArn"]

    @property
    def _shots(self) -> int:
        """Return the number of repetitions used in the run"""
        return self.vendor_jlo.metadata()["shots"]

    def _status(self):
        """Returns status from Braket QuantumTask object metadata."""
        return self.vendor_jlo.metadata()["status"]

    def ended_at(self):
        """The time when the job ended."""
        return self.vendor_jlo.metadata()["endedAt"]

    def result(self) -> Union[AnnealingQuantumTaskResult, GateModelQuantumTaskResult]:
        """Return the results of the job."""
        return self.vendor_jlo.result()

    def async_result(self) -> Task:
        """asyncio.Task: Get the quantum task result asynchronously."""
        return self.vendor_jlo.async_result()

    def cancel(self):
        """Cancel the quantum task."""
        return self.vendor_jlo.cancel()

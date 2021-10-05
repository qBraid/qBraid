"""BraketQuantumtaskWrapper Class"""

from __future__ import annotations

from asyncio import Task
from typing import Union

from braket.tasks import QuantumTask
from braket.tasks.annealing_quantum_task_result import AnnealingQuantumTaskResult
from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult

from qbraid.devices.job import JobLikeWrapper


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

    def _set_static(self):
        self._vendor_metadata = self.vendor_jlo.metadata()
        return {
            "shots": self._vendor_metadata["shots"],
            "vendor_job_id": self._vendor_metadata["quantumTaskArn"],
            "createdAt": self._vendor_metadata["createdAt"],
            "endedAt": None,
        }

    def status(self):
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

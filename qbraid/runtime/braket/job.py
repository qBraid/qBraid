# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining BraketQuantumTask Class

"""
import logging
from typing import Optional, Union

from braket.aws import AwsQuantumTask
from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import (
    AnalogHamiltonianSimulationQuantumTaskResult,
)
from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError
from qbraid.runtime.job import QuantumJob

from .result import BraketAhsJobResult, BraketGateModelJobResult
from .tracker import get_quantum_task_cost

logger = logging.getLogger(__name__)

AWS_TASK_STATUS_MAP = {
    "CREATED": JobStatus.INITIALIZING,
    "QUEUED": JobStatus.QUEUED,
    "RUNNING": JobStatus.RUNNING,
    "CANCELLING": JobStatus.CANCELLING,
    "CANCELLED": JobStatus.CANCELLED,
    "COMPLETED": JobStatus.COMPLETED,
    "FAILED": JobStatus.FAILED,
}


class AmazonBraketVersionError(Exception):
    """Exception raised for Amazon Braket SDK errors due to versioning."""


class BraketQuantumTask(QuantumJob):
    """Wrapper class for Amazon Braket ``QuantumTask`` objects."""

    def __init__(self, task_id: str, task: Optional[AwsQuantumTask] = None, **kwargs):
        """Create a BraketQuantumTask."""

        super().__init__(task_id, **kwargs)
        self._task = task or AwsQuantumTask(task_id)

    def status(self):
        """Returns status from Braket QuantumTask object metadata."""
        state = self._task.state()
        status = AWS_TASK_STATUS_MAP.get(state, JobStatus.UNKNOWN)
        self._cache_metadata["status"] = status
        return status

    def queue_position(self) -> Optional[int]:
        """Returns queue position from Braket QuantumTask.
        '>2000' returns as 2000 for typing consistency."""
        try:
            position = self._task.queue_position().queue_position
            if isinstance(position, str):
                if position.startswith(">"):
                    position = position[1:]
                return int(position)
            return position
        except AttributeError as err:
            raise AmazonBraketVersionError(
                "Queue visibility is only available for amazon-braket-sdk>=1.56.0"
            ) from err

    def result(self) -> Union[BraketGateModelJobResult, BraketAhsJobResult]:
        """
        Return the results of the job. Raises a RuntimeError if the job is not in a terminal state.
        """
        if not self.is_terminal_state():
            logger.info("Result will be available when the job has reached a final state.")

        result = self._task.result()

        result_class_mapping = {
            GateModelQuantumTaskResult: BraketGateModelJobResult,
            AnalogHamiltonianSimulationQuantumTaskResult: BraketAhsJobResult,
        }
        result_class = type(result)
        if result_class in result_class_mapping:
            return result_class_mapping[result_class](result)

        raise ValueError(f"Unsupported result type: {result_class.__name__}")

    def cancel(self) -> None:
        """Cancel the quantum task."""
        task = self._task

        if self.is_terminal_state():
            raise JobStateError("Cannot cancel quantum job in terminal state.")

        try:
            task.cancel()
        except RuntimeError:
            task._aws_session.cancel_quantum_task(task.arn)

    def get_cost(self) -> float:
        """Return the cost of the job."""
        decimal_cost = get_quantum_task_cost(self._task.arn)
        return float(decimal_cost)

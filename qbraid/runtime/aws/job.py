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
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import boto3
from braket.aws import AwsQuantumTask
from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import (
    AnalogHamiltonianSimulationQuantumTaskResult,
)
from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult

from qbraid._logging import logger
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import AhsResultData, GateModelResultData

from .result_builder import BraketAhsResultBuilder, BraketGateModelResultBuilder
from .tracker import get_quantum_task_cost

if TYPE_CHECKING:
    from decimal import Decimal

    from braket.aws import AwsSession

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

    def result(self) -> Result:
        """Return the results of the job."""
        if not self.is_terminal_state():
            logger.info("Result will be available when the job has reached a final state.")

        bk_result = self._task.result()
        metadata = self._task.metadata()
        success = metadata["status"] == "COMPLETED"
        device_id = metadata["deviceArn"]
        job_id = metadata["quantumTaskArn"]

        result_mapping = {
            GateModelQuantumTaskResult: (BraketGateModelResultBuilder, GateModelResultData),
            AnalogHamiltonianSimulationQuantumTaskResult: (BraketAhsResultBuilder, AhsResultData),
        }

        builder_class, data_class = result_mapping.get(type(bk_result), (None, None))

        if not builder_class or not data_class:
            raise ValueError(f"Unsupported result type: {type(bk_result).__name__}")

        # Retrieve partial measurement qubit information from job tags
        partial_measurement_qubits = self._get_partial_measurement_qubits_from_tags(
            bk_result.measured_qubits
        )
        result_data = {
            "measurement_counts": (
                builder_class(bk_result, partial_measurement_qubits).get_counts()
                if success
                else None
            ),
            "measurements": (
                builder_class(bk_result, partial_measurement_qubits).measurements()
                if success
                else None
            ),
        }

        data = data_class(**result_data)
        return Result(device_id=device_id, job_id=job_id, success=success, data=data, **metadata)

    def cancel(self) -> None:
        """Cancel the quantum task."""
        task = self._task

        if self.is_terminal_state():
            raise JobStateError("Cannot cancel quantum job in terminal state.")

        try:
            task.cancel()
        except RuntimeError:
            task._aws_session.cancel_quantum_task(self.id)

    @staticmethod
    def _get_cost(task_arn: str, aws_session: Optional[AwsSession] = None) -> Decimal:
        """Return the cost of the quantum task."""
        return get_quantum_task_cost(task_arn, aws_session=aws_session)

    def get_cost(self) -> float:
        """Return the cost of the job."""
        decimal_cost = self._get_cost(self.id)
        return float(decimal_cost)

    def _get_partial_measurement_qubits_from_tags(
        self, all_measurement_qubits: list[int]
    ) -> list[int] | None:
        """
        Retrieve partial measurement qubit indices from quantum task tags.

        This method queries the AWS Braket service to get the quantum task metadata
        and extracts the partial measurement qubit information that was stored as tags
        during task submission. It then maps these qubit indices to their positions
        in the measurement results array.

        Args:
            all_measurement_qubits: List of all qubits that were measured in the circuit,
                in the order they appear in the measurement results.

        Returns:
            List of indices corresponding to the positions of partial measurement qubits
            in the measurement results array, or None if no partial measurements were used.
        """
        braket_client = boto3.client("braket", region_name=self._task._aws_session.region)
        response = braket_client.get_quantum_task(quantumTaskArn=self._task.id)

        if "partial_measurement_qubits" not in response["tags"]:
            return None

        # Parse the partial measurement qubit indices from the tag string (e.g., "0/2/3")
        partial_measurement_qubits_str = response["tags"]["partial_measurement_qubits"]
        partial_measurement_qubits = [int(q) for q in partial_measurement_qubits_str.split("/")]

        # Map the original qubit indices to their positions in the measurement results array
        partial_measurement_qubit_indices = [
            all_measurement_qubits.index(q) for q in partial_measurement_qubits
        ]
        return partial_measurement_qubit_indices

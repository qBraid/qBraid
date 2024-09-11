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
from collections import Counter
from typing import Optional

import numpy as np
from braket.aws import AwsQuantumTask
from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import (
    AnalogHamiltonianSimulationQuantumTaskResult,
    AnalogHamiltonianSimulationShotStatus,
    ShotResult,
)
from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult

from qbraid.runtime.enums import ExperimentType, JobStatus
from qbraid.runtime.exceptions import JobStateError, ResultDecodingError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import ExperimentalResult, RuntimeJobResult

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

    def _build_gate_model_results(self, job_data):
        braket_counts = dict(job_data.measurement_counts)
        qbraid_counts = {}
        for key in braket_counts:
            str_key = "".join(reversed([str(i) for i in key]))
            qbraid_counts[str_key] = braket_counts[key]

        return [
            ExperimentalResult(
                counts=qbraid_counts,
                measurements=np.flip(job_data.measurements, 1),
                result_type=ExperimentType.GATE_MODEL,
                metadata=job_data.task_metadata,
            )
        ]

    def _build_ahs_results(self, job_data):
        measurements = []
        for measurement in job_data.measurements:
            status = AnalogHamiltonianSimulationShotStatus(measurement.shotMetadata.shotStatus)
            pre_sequence = None
            if measurement.shotResult.preSequence:
                pre_sequence = np.asarray(measurement.shotResult.preSequence, dtype=int)

            post_sequence = None
            if measurement.shotResult.postSequence:
                post_sequence = np.asarray(measurement.shotResult.postSequence, dtype=int)

            measurements.append(ShotResult(status, pre_sequence, post_sequence))

        counts = Counter()
        states = ["e", "r", "g"]
        try:
            for shot in measurements:
                if shot.status == AnalogHamiltonianSimulationShotStatus.SUCCESS:
                    pre = shot.pre_sequence
                    post = shot.post_sequence
                    # converting presequence and postsequence measurements to state_idx
                    state_idx = [
                        0 if pre_i == 0 else 1 if post_i == 0 else 2
                        for pre_i, post_i in zip(pre, post)
                    ]
                    state = "".join(states[s_idx] for s_idx in state_idx)
                    counts.update([state])
        except Exception as err:
            raise ResultDecodingError from err

        counts = None if not counts else dict(counts)

        return [
            ExperimentalResult(
                counts=counts,
                measurements=measurements,
                result_type=ExperimentType.AHS,
                metadata=job_data.task_metadata,
            )
        ]

    def result(self) -> RuntimeJobResult:
        """
        Return the results of the job. Raises a RuntimeError if the job is not in a terminal state.
        """
        if not self.is_terminal_state():
            logger.info("Result will be available when the job has reached a final state.")

        result = self._task.result()

        if isinstance(result, GateModelQuantumTaskResult):
            exp_results = self._build_gate_model_results(result)
        elif isinstance(result, AnalogHamiltonianSimulationQuantumTaskResult):
            exp_results = self._build_ahs_results(result)
        else:
            raise ValueError(f"Unsupported result type: {type(result).__name__}")

        return RuntimeJobResult(
            job_id=result.task_metadata.id,
            device_id=result.task_metadata.deviceId,
            results=exp_results,
            success=result.task_metadata.status == "COMPLETED",
        )

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

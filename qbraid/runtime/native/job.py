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
Module defining QbraidJob class

"""
import logging
from typing import TYPE_CHECKING, Any, Optional

from qbraid_core.services.quantum import QuantumClient

from qbraid.runtime.enums import ExperimentType, JobStatus
from qbraid.runtime.exceptions import JobStateError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import ExperimentalResult, ResultFormatter, RuntimeJobResult

if TYPE_CHECKING:
    import qbraid_core.services.quantum

    import qbraid.runtime

logger = logging.getLogger(__name__)


class QbraidJob(QuantumJob):
    """Class representing a qBraid job."""

    def __init__(
        self,
        job_id: str,
        device: "Optional[qbraid.runtime.QbraidDevice]" = None,
        client: "Optional[qbraid_core.services.quantum.QuantumClient]" = None,
        **kwargs,
    ):
        super().__init__(job_id, device, **kwargs)
        self._client = client

    @property
    def client(self) -> "qbraid_core.services.quantum.QuantumClient":
        """
        Lazily initializes and returns the client object associated with the job.
        If the job has an associated device with a client, that client is used.
        Otherwise, a new instance of QuantumClient is created and used.

        Returns:
            QuantumClient: The client object associated with the job.
        """
        if self._client is None:
            self._client = self._device.client if self._device else QuantumClient()
        return self._client

    @staticmethod
    def _map_status(status: Optional[str]) -> JobStatus:
        """Returns `JobStatus` object mapped from raw status value. If no value
        provided or conversion from string fails, returns `JobStatus.UNKNOWN`."""
        if status is None:
            return JobStatus.UNKNOWN
        if not isinstance(status, str):
            raise ValueError(f"Invalid status value type: {type(status)}")
        for e in JobStatus:
            status_enum = JobStatus(e.value)
            if status == status_enum.name or status == str(status_enum):
                return status_enum
        raise ValueError(f"Status value '{status}' not recognized.")

    def status(self) -> JobStatus:
        """Return the status of the job / task , among the values of ``JobStatus``."""
        job_data = self.client.get_job(self.id)
        status = job_data.get("status")
        return self._map_status(status)

    def cancel(self) -> None:
        """Attempt to cancel the job."""
        if self.is_terminal_state():
            raise JobStateError("Cannot cancel job in a terminal state.")

        self.client.cancel_job(self.id)

    def _build_runtime_gate_model_results(self, job_data, **kwargs) -> list[ExperimentalResult]:
        """Build and return the results of a gate-model simulation.

        Args:
            job_data (dict): The job data dictionary.
        """
        measurement_counts = job_data.get("measurementCounts", {})
        time_stamps: dict[str, Any] = job_data.get("timeStamps", {})
        execution_duration: int = time_stamps.get("executionDuration", -1)
        return [
            ExperimentalResult(
                state_counts=measurement_counts,
                measurements=ResultFormatter.counts_to_measurements(measurement_counts),
                result_type=ExperimentType.GATE_MODEL,
                execution_duration=execution_duration,
                metadata=None,
            )
        ]

    def result(self) -> "qbraid.runtime.RuntimeJobResult":
        """Return the results of the job."""
        self.wait_for_final_state()
        job_data = self.client.get_job(self.id)
        device_id: str = job_data.get("qbraidDeviceId")
        success: bool = job_data.get("status") == "COMPLETED"
        experiment_results = self.build_runtime_result(ExperimentType.GATE_MODEL, job_data)
        return RuntimeJobResult(self.id, device_id, experiment_results, success)

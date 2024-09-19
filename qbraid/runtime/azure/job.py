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
Module defining AzureQuantumJob class

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from azure.quantum.target.microsoft import MicrosoftEstimatorResult

from qbraid._logging import logger
from qbraid.runtime.azure.result_builder import AzureGateModelResultBuilder
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import GateModelResultData, Result

from .io_format import OutputDataFormat

if TYPE_CHECKING:
    import azure.quantum


class AzureQuantumJob(QuantumJob):
    """Azure job class."""

    def __init__(self, job_id: str, workspace: azure.quantum.Workspace, **kwargs):
        super().__init__(job_id=job_id, **kwargs)
        self._workspace = workspace
        self._job = self.workspace.get_job(self.id)

    @property
    def workspace(self) -> azure.quantum.Workspace:
        """Return the Azure Quantum Workspace."""
        return self._workspace

    def _details(self) -> dict[str, Any]:
        """Return the details of the Azure job and
        update the metadata cache."""
        self._job.refresh()
        details = self._job.details.as_dict()
        self._cache_metadata["details"] = details
        return details

    def status(self) -> JobStatus:
        """Return the current status of the Azure job.

        Returns:
            JobStatus: The current status of the job.
        """
        details: dict = self._details()
        status: str = details.get("status")

        status_map = {
            "Succeeded": JobStatus.COMPLETED,
            "Waiting": JobStatus.QUEUED,
            "Executing": JobStatus.RUNNING,
            "Failed": JobStatus.FAILED,
            "Cancelled": JobStatus.CANCELLED,
            "Finishing": JobStatus.RUNNING,
        }
        return status_map.get(status, JobStatus.UNKNOWN)

    @staticmethod
    def _make_estimator_result(data: dict[str, Any]) -> MicrosoftEstimatorResult:
        """Create a MicrosoftEstimatorResult from the given data.

        Args:
            data (dict): The data to create the result from.

        Returns:
            MicrosoftEstimatorResult: The result created from the data.

        Raises:
            RuntimeError: If the job execution failed.
        """
        if not data["success"]:
            error_data = data["error_data"]
            raise RuntimeError(
                f"Cannot retrieve results as job execution failed "
                f"({error_data['code']}: {error_data['message']})"
            )

        result_data = data["data"]
        return MicrosoftEstimatorResult(result_data)

    def result(self) -> Union[Result, MicrosoftEstimatorResult]:
        """Return the result of the Azure job.

        Returns:
            Union[Result, MicrosoftEstimatorResult]: The result of the job.
        """
        if not self.is_terminal_state():
            logger.info("Result will be available when job has reached final state.")

        job: azure.quantum.Job = self._job
        job.wait_until_completed()

        success = job.details.status == "Succeeded"
        details = job.details.as_dict()

        if job.details.output_data_format == OutputDataFormat.RESOURCE_ESTIMATOR.value:
            return self._make_estimator_result(
                {
                    "job_id": job.id,
                    "target": job.details.target,
                    "job_name": job.details.name,
                    "success": success,
                    "data": job.get_results(),
                    "error_data": (
                        None if job.details.error_data is None else job.details.error_data.as_dict()
                    ),
                }
            )

        builder = AzureGateModelResultBuilder(job)
        data = GateModelResultData(measurement_counts=builder.get_counts())
        return Result(
            device_id=job.details.target, job_id=job.id, success=success, data=data, **details
        )

    def cancel(self) -> None:
        """Cancel the Azure job."""
        if self.is_terminal_state():
            raise JobStateError("Cannot cancel; job in terminal state.")

        self._job = self.workspace.cancel_job(self._job)

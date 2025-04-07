# Copyright (C) 2025 qBraid
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

from typing import TYPE_CHECKING, Any, Optional, Union


from azure.quantum.workspace import Workspace

from qbraid._logging import logger
from qbraid.runtime.azure.result_builder import (
    AzureAHSModelResultBuilder,
    AzureGateModelResultBuilder,
)
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import AhsResultData, GateModelResultData

from .io_format import OutputDataFormat

if TYPE_CHECKING:
    import azure.quantum


class AzureQuantumJob(QuantumJob):
    """Azure job class."""

    def __init__(self, job_id: str, workspace: Optional[Workspace] = None, **kwargs):
        super().__init__(job_id=job_id, **kwargs)
        self._workspace = workspace or Workspace()
        self._job = self.workspace.get_job(self.id)

    @property
    def workspace(self) -> azure.quantum.Workspace:
        """Return the Azure Quantum Workspace."""
        return self._workspace

    def details(self) -> dict[str, Any]:
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
        details: dict = self.details()
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

    def result(self, wait_until_completed=False) -> Union[Result]:
        """Return the result of the Azure job.

        Args:
            wait_until_completed (bool, optional): If True, waits until the job is completed 
                before retrieving the result. Defaults to False.

        Returns:
            Union[Result]: The result of the job.
        """
        if not self.is_terminal_state():
            logger.info("Result will be available when job has reached final state.")

        job: azure.quantum.Job = self._job
        if wait_until_completed:
            job.wait_until_completed()

        success = job.details.status == "Succeeded"
        details = job.details.as_dict()

        if job.details.output_data_format == OutputDataFormat.PASQAL.value:
            builder = AzureAHSModelResultBuilder(job)
            data = AhsResultData(measurement_counts=builder.get_counts())
            return Result(
                device_id=job.details.target, job_id=job.id, success=success, data=data, **details
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

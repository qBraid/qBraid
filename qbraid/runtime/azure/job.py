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
Module defining Azure job class

"""
import logging
from typing import TYPE_CHECKING, Any, Union

from qbraid.runtime.azure.result import AzureQuantumResult
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError
from qbraid.runtime.job import QuantumJob

if TYPE_CHECKING:
    import azure.quantum


logger = logging.getLogger(__name__)


class AzureQuantumJob(QuantumJob):
    """Azure job class."""

    def __init__(self, job_id: str, workspace: "azure.quantum.Workspace", **kwargs):
        super().__init__(job_id=job_id, **kwargs)
        self._workspace = workspace
        self._job = self.workspace.get_job(self.id)

    @property
    def workspace(self) -> "azure.quantum.Workspace":
        """Return the Azure Quantum Workspace."""
        return self._workspace

    def status(self) -> JobStatus:
        """Return the current status of the Azure job.

        Returns:
            JobStatus: The current status of the job.
        """
        self._job.refresh()
        status: str = self._job.details.status

        status_map = {
            "Waiting": JobStatus.QUEUED,
            "Executing": JobStatus.RUNNING,
            "Failed": JobStatus.FAILED,
            "Cancelled": JobStatus.CANCELLED,
            "Succeeded": JobStatus.COMPLETED,
        }
        return status_map.get(status, JobStatus.UNKNOWN)

    def result(self) -> AzureQuantumResult:
        """Return the result of the Azure job.

        Returns:
            str: The result of the job.
        """
        if not self.is_terminal_state():
            logger.info("Result will be available when job has reached final state.")

        result: Union[dict[str, float], Any] = self._job.get_results()

        if "meas" not in result:
            raise RuntimeError("No measurement results found.")

        return AzureQuantumResult(result)

    def cancel(self) -> None:
        """Cancel the Azure job."""
        if self.is_terminal_state():
            raise JobStateError("Cannot cancel; job in terminal state.")

        self._job = self.workspace.cancel_job(self._job)

        logger.info("Job canceled successfully.")

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

import logging
from typing import TYPE_CHECKING, Any, Union

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError
from qbraid.runtime.job import QuantumJob

from .result_builder import AzureResultBuilder

if TYPE_CHECKING:
    import azure.quantum
    from azure.quantum.target.microsoft import MicrosoftEstimatorResult

    from qbraid.runtime.azure.result import AzureGateModelResultBuilder


logger = logging.getLogger(__name__)


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

    def result(self) -> Union[AzureGateModelResultBuilder, MicrosoftEstimatorResult]:
        """Return the result of the Azure job.

        Returns:
            Union[AzureGateModelResultBuilder, MicrosoftEstimatorResult]: The result of the job.
        """
        if not self.is_terminal_state():
            logger.info("Result will be available when job has reached final state.")

        builder = AzureResultBuilder(self._job)

        return builder.result()

    def cancel(self) -> None:
        """Cancel the Azure job."""
        if self.is_terminal_state():
            raise JobStateError("Cannot cancel; job in terminal state.")

        self._job = self.workspace.cancel_job(self._job)

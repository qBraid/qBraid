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
from typing import TYPE_CHECKING

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError
from qbraid.runtime.job import QuantumJob

if TYPE_CHECKING:
    import qbraid.runtime.azure


class AzureJob(QuantumJob):
    """Azure job class."""

    def __init__(self, job_id: str, client: "qbraid.runtime.azure.AzureClient", **kwargs):
        super().__init__(job_id=job_id, **kwargs)
        self._client = client

    @property
    def client(self) -> "qbraid.runtime.azure.AzureClient":
        """Return the Azure client."""
        return self._client

    def status(self) -> JobStatus:
        """Return the current status of the Azure job."""
        job_info = self.client.get_job(self.id)
        status = job_info.get("status")

        status_map = {
            "Waiting": JobStatus.QUEUED,
            "Executing": JobStatus.RUNNING,
            "Failed": JobStatus.FAILED,
            "Cancelled": JobStatus.CANCELLED,
            "Succeeded": JobStatus.COMPLETED,
        }
        return status_map.get(status, JobStatus.UNKNOWN)

    def cancel(self) -> None:
        """Cancel the Azure job."""
        self.client.cancel_job(self.id)

    def result(self) -> str:
        """Return the result of the Azure job."""
        self.wait_for_final_state()
        status = self.status()

        if not status == JobStatus.COMPLETED:
            job_data = self.client.get_job(self.id)
            failure: dict = job_data.get("Failed", {})
            code = failure.get("code")
            message = failure.get("error")
            raise JobStateError(f"Job failed with code {code}: {message}")

        blob_service_client = self.client.service
        container_client = blob_service_client.get_container_client(f"job-{self.id}")
        blob_client = container_client.get_blob_client("rawOutputData")
        return blob_client.download_blob().readall().decode("utf-8")

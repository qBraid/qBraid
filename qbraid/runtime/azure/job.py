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

from azure.storage.blob import BlobServiceClient

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.job import QuantumJob

if TYPE_CHECKING:
    import qbraid.runtime.azure.provider


class AzureJob(QuantumJob):
    """Azure job class."""

    def __init__(
        self, job_id: str, session: "qbraid.runtime.azure.provider.AzureSession", **kwargs
    ):
        super().__init__(job_id=job_id, **kwargs)
        self._session = session

    @property
    def session(self) -> "qbraid.runtime.azure.provider.AzureSession":
        """Return the Azure session."""
        return self._session

    def get_job_info(self):
        """Get the information for the Azure job."""

        url = (
            f"https://{self._session.auth_data.location_name}.quantum.azure.com/"
            f"subscriptions/{self._session.auth_data.subscription_id}/"
            f"resourceGroups/{self._session.auth_data.resource_group}/"
            f"providers/Microsoft.Quantum/workspaces/"
            f"{self._session.auth_data.workspace_name}/jobs/{self._job_id}"
            f"?api-version=2022-09-12-preview"
        )

        response = self._session.get(url)
        return response.json()

    def status(self) -> JobStatus:
        """Return the current status of the Azure job."""
        job_info = self.get_job_info()
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
        response = self._session.delete(self._job_id)
        return response

    def result(self) -> dict:
        """Return the result of the Azure job."""
        self.wait_for_final_state()
        job_info = self.get_job_info()

        success = job_info.get("status") == "Succeeded"

        if not success:
            failure: dict = job_info.get("Failed", {})
            code = failure.get("code")
            message = failure.get("error")
            raise ValueError(f"Job failed with code {code}: {message}")

        blob_service_client = BlobServiceClient.from_connection_string(
            self._session.auth_data.api_connection
        )
        container_client = blob_service_client.get_container_client(f"job-{self._job_id}")
        blob_client = container_client.get_blob_client("rawOutputData")
        blob_data = blob_client.download_blob().readall().decode("utf-8")

        return blob_data

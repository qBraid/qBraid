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
Module defining Azure Quantum device class for all devices managed by Azure Quantum.

"""

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from azure.storage.blob import BlobServiceClient, ContentSettings

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import AzureJob
from .session import ResourceScope

if TYPE_CHECKING:
    import qbraid.runtime
    from qbraid.runtime.azure.session import AzureSession


class AzureQuantumDevice(QuantumDevice):
    """Azure quantum device interface."""

    def __init__(
        self,
        profile: "qbraid.runtime.TargetProfile",
        session: "AzureSession",
    ):
        super().__init__(profile=profile)
        self._session = session
        self.backends = {
            "Syntax-Checker": "quantinuum.sim.h1-1sc",
            "Emulator": "quantinuum.sim.h1-1e",
            "QPU": "quantinuum.qpu.h1-1",
        }  # will need to add for pyquil
        self.formats = {"quantinuum": ["honeywell.openqasm.v1", "honeywell.quantum-results.v1"]}
        self.type = ""

    @property
    def session(self) -> "AzureSession":
        """Return the Azure session."""
        return self._session

    def status(self) -> "qbraid.runtime.enums.DeviceStatus":
        """Return the current status of the Azure device."""
        status = self.profile.get("status")
        status_map = {
            "Available": DeviceStatus.ONLINE,
            "Deprecated": DeviceStatus.UNAVAILABLE,
            "Unavailable": DeviceStatus.OFFLINE,
        }
        return status_map.get(status)

    def submit(self, input_run: Any, name: str, backend: str, qubits: int, num_shots: int = 100):
        """Submit a job to the Azure device."""

        # is_single_input = not isinstance(run_input, list)
        # run_input = [run_input] if is_single_input else run_input
        if isinstance(input_run, list):
            raise ValueError(
                "Batch jobs (list of inputs) are not supported for this device. "
                "Please provide a single job input."
            )

        device_type = self.profile.get("device_id").split(".")[0]

        container = self.create_container()

        job_id = container[0]
        container_name = container[1]

        job = input_run

        routes = self.create_job_routes(container_name, job)

        container_sas_uri = routes[0]
        input_sas_uri = routes[1]
        output_sas_uri = routes[2]

        payload = self.create_payload(
            container_sas_uri,
            input_sas_uri,
            output_sas_uri,
            job_id,
            job_name=name,
            input_data_format=self.formats[device_type][0],
            provider=device_type,
            backend=self.backends[backend],
            num_qubits=qubits,
            num_shots=num_shots,
            total_count=100,
            output_data_format=self.formats[device_type][1],
        )

        url = (
            f"https://{self._session.auth_data.location_name}.quantum.azure.com/"
            f"subscriptions/{self._session.auth_data.subscription_id}/"
            f"resourceGroups/{self._session.auth_data.resource_group}/"
            f"providers/Microsoft.Quantum/workspaces/"
            f"{self._session.auth_data.workspace_name}/jobs/{job_id}"
            f"?api-version=2022-09-12-preview"
        )

        response = self._session.put(url, payload=payload, put_type="quantum")
        submitted_job = AzureJob(job_id=job_id, session=self._session)

        return [response.json(), submitted_job]

    def create_container(self) -> list[str]:
        """Create a new container for the job."""

        job_id = str(uuid4())
        container_name = f"job-{job_id}"  # name of the container to create

        auth_data = self._session.auth_data

        url = (
            f"https://management.azure.com/"
            f"subscriptions/{auth_data.subscription_id}/"
            f"resourceGroups/{auth_data.resource_group}/"
            f"providers/Microsoft.Storage/storageAccounts/{auth_data.storage_account}/"
            f"blobServices/default/containers/{container_name}"
            f"?api-version=2022-09-01"
        )

        self._session.put(url, payload={}, put_type=ResourceScope.MANAGEMENT)
        return [job_id, container_name]

    def create_job_routes(self, container: str, qasm: str) -> list[str]:
        """Create the routes for the job."""

        blob_service_client = BlobServiceClient.from_connection_string(
            self._session.auth_data.api_connection
        )

        blob_client = blob_service_client.get_blob_client(container, "inputData")
        blob_client.upload_blob(
            qasm, content_settings=ContentSettings(content_type="application/qasm")
        )

        blob_client = blob_service_client.get_blob_client(container, "rawOutputData")
        blob_client.upload_blob("")

        payload = {"containerName": container}

        response = self._session.post(payload=payload)
        container_sas_uri = response.json()["sasUri"]

        payload["blobName"] = "inputData"
        response = self._session.post(payload=payload)
        input_sas_uri = response.json()["sasUri"]

        payload["blobName"] = "rawOutputData"
        response = self._session.post(payload=payload)
        ouput_sas_uri = response.json()["sasUri"]

        return [container_sas_uri, input_sas_uri, ouput_sas_uri]

    def create_payload(
        self,
        container_uri: str,
        input_uri: str,
        output_uri: str,
        job_id: str,
        job_name: str,
        input_data_format: str,
        provider: str,
        backend: str,
        num_qubits: str,
        num_shots: int,
        total_count: int,
        output_data_format: str,
    ) -> dict:
        """Create the payload for the job."""
        payload = {
            "containerUri": container_uri,
            "id": job_id,
            "inputDataFormat": input_data_format,  # "honeywell.openqasm.v1"
            "itemType": "Job",
            "name": job_name,
            "providerId": provider,
            "target": backend,  # changeable
            "metadata": {
                "qiskit": "True",
                "name": job_name,
                "num_qubits": num_qubits,
                "metadata": "null",
                "meas_map": "[0]",
            },
            "inputDataUri": input_uri,
            "inputParams": {"shots": num_shots, "count": total_count},
            "outputDataFormat": output_data_format,  # "honeywell.quantum-results.v1"
            "outputDataUri": output_uri,
        }

        return payload

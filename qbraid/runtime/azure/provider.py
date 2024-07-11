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
Module defining Azure session and provider classes

"""
from typing import Any
from uuid import uuid4

import openqasm3
from azure.storage.blob import BlobServiceClient, ContentSettings
from qbraid_core._import import LazyLoader
from qbraid_core.sessions import Session

from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.enums import DeviceType
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import AzureQuantumDevice

pyquil = LazyLoader("pyquil", globals(), "pyquil")


class AzureSession(Session):
    """Azure session class."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        location_name: str,
        subscription_id: str,
        resource_group_name: str,
        workspace_name: str,
        storage_account: str,
        connection_string: str,
    ):  # pylint: disable= too-many-arguments

        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.location_name = location_name
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.workspace_name = workspace_name
        self.storage_account = storage_account
        self.connection_string = connection_string
        self.backends = {
            "Syntax Checker": "quantinuum.sim.h1-1sc",
            "Emulator": "quantinuum.sim.h1-1e",
            "QPU": "quantinuum.qpu.h1-1",
        }  # will need to add for pyquil
        self.formats = {"quantinuum": ["honeywell.openqasm.v1", "honeywell.quantum-results.v1"]}

        self.jobs = {}
        self.session = Session()
        self._helpers = AzureHelperFunctions()

        self.base_url = (f"https://{location_name}.quantum.azure.com",)

        super().__init__(base_url=self.base_url)

    def get_devices(self) -> list[str, dict[str, Any]]:
        """Get all Azure Quantum devices."""
        quantum_access_token = self._helpers.quantum_access_token(
            self.client_id, self.client_secret, self.tenant_id, self.session
        )

        url = (
            f"https://{self.location_name}.quantum.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group_name}/providers/Microsoft.Quantum/"
            f"workspaces/{self.workspace_name}/providerStatus?api-version=2022-09-12-preview"
        )

        auth_headers = {"Authorization": f"Bearer {quantum_access_token}"}
        r = self.session.get(url, headers=auth_headers)
        devices = r.json()

        devices_dict = self._helpers.device_manager(devices)
        devices_list = [{"id": k, **v} for k, v in devices_dict.items()]

        return devices_list

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Get a specific Azure Quantum device."""
        devices = self.get_devices()
        device = None

        for i in devices:
            if i.get("id") == device_id:
                device = i

        return device

    # pylint: disable=too-many-arguments
    def create_job(
        self, input_run: Any, name: str, provider: str, backend: str, qubits: int
    ) -> dict[str, Any]:
        """Create a new job on the Azure Quantum API."""
        quantum_access_token = self._helpers.quantum_access_token(
            self.client_id, self.client_secret, self.tenant_id, self.session
        )

        storage_access_token = self._helpers.storage_access_token(
            self.client_id, self.client_secret, self.tenant_id, self.session
        )

        container = self._helpers.create_container(
            storage_access_token,
            self.subscription_id,
            self.resource_group_name,
            self.storage_account,
            self.session,
        )

        job_id = container[0]
        container_name = container[1]

        job = input_run
        routes = self._helpers.create_job_routes(
            self.session,
            container_name,
            job,
            self.connection_string,
            self.location_name,
            self.subscription_id,
            self.resource_group_name,
            self.workspace_name,
            quantum_access_token,
        )

        containerSasUri = routes[0]
        inputSasUri = routes[1]
        outputSasUri = routes[2]
        job_headers = routes[3]

        job_payload = self._helpers.create_payload(
            containerSasUri,
            inputSasUri,
            outputSasUri,
            job_id,
            job_name=name,
            input_data_format=self.formats[provider][0],
            provider=provider,
            backend=self.backends[backend],
            num_qubits=qubits,
            num_shots=100,
            total_count=100,
            output_data_format=self.formats[provider][1],
        )

        job_approval = self._helpers.submit_job(
            job_id,
            job_payload,
            job_headers,
            self.location_name,
            self.subscription_id,
            self.resource_group_name,
            self.workspace_name,
            self.session,
        )

        self.jobs[job_id] = [job_headers, container_name]

        return job_approval

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Get a specific Azure Quantum job."""

        job = job_id
        header = self.jobs[job_id][0]
        url = (
            f"https://{self.location_name}.quantum.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group_name}/providers/Microsoft.Quantum/workspaces/"
            f"{self.workspace_name}/jobs/{job}?api-version=2022-09-12-preview"
        )

        response = self.session.get(url, headers=header)
        return response.json()

    def get_job_data(self, job_id: str) -> dict[str, Any]:
        """Get the data from a specific Azure Quantum job."""

        data = self._helpers.get_output_data(f"{self.jobs[job_id][1]}", self.connection_string)
        return data

    def cancel_job(self, job_id: str):
        """Cancel a specific Azure Quantum job."""
        job = job_id
        header = self.jobs[job_id][0]
        url = (
            f"https://{self.location_name}.quantum.azure.com/subscriptions/"
            f"{self.subscription_id}/resourceGroups/{self.resource_group_name}/"
            f"providers/Microsoft.Quantum/workspaces/{self.workspace_name}/jobs/"
            f"{job}?api-version=2022-09-12-preview"
        )

        response = self.session.delete(url, headers=header)
        print("Job has been cancelled.")
        return str(response)


class AzureQuantumProvider(QuantumProvider):
    """Azure provider class."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        location_name: str,
        subscription_id: str,
        resource_group_name: str,
        workspace_name: str,
        storage_account: str,
        connection_string: str,
    ):  # pylint: disable= too-many-arguments
        super().__init__()
        self.session = AzureSession(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            location_name=location_name,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            workspace_name=workspace_name,
            storage_account=storage_account,
            connection_string=connection_string,
        )

    def _build_profile(self, data: dict[str, Any]) -> TargetProfile:
        """Build a profile for an Azure device."""

        device = data.get("id")

        if "qpu" not in device:
            device_type = DeviceType.SIMULATOR
        else:
            device_type = DeviceType.QPU

        if "rigetti" in device:
            program_spec = ProgramSpec(pyquil.Program)
        else:
            program_spec = ProgramSpec(openqasm3.ast.Program)

        queue_time = data.get("averageQueueTime")
        status = data.get("status")

        return TargetProfile(
            device_id=data.get("id"),
            device_type=device_type,
            program_spec=program_spec,
            queue_time=queue_time,
            status=status,
        )

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Get a specific Azure device."""
        data = self.session.get_device(device_id)
        profile = self._build_profile(data)
        return AzureQuantumDevice(profile, self.session)

    def get_devices(self, **kwargs) -> list[AzureQuantumDevice]:
        """Get a list of Azure devices."""
        devices = self.session.get_devices()

        quantum_devices = [
            AzureQuantumDevice(self._build_profile(device), self.session) for device in devices
        ]
        return quantum_devices


class AzureHelperFunctions:
    """Helper functions for Azure Quantum API."""

    def quantum_access_token(
        self, client_id: str, client_secret: str, tenant_id: str, session: Any
    ) -> str:
        """Generates access token for Azure Quantum API."""
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://quantum.microsoft.com/.default",
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        r = session.post(url, headers=headers, data=data, verify=True)
        quantum_access_token = r.json()["access_token"]

        return quantum_access_token

    def storage_access_token(
        self, client_id: str, client_secret: str, tenant_id: str, session: Any
    ) -> str:
        """Generates access token for Azure Storage API."""
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://management.azure.com/.default",
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        r = session.post(url, headers=headers, data=data, verify=True)
        storage_access_token = r.json()["access_token"]

        return storage_access_token

    @staticmethod
    def device_manager(devices: dict) -> dict[str, dict[str, Any]]:
        """Manages the data for all Azure Quantum devices."""
        devices_dict = {}

        for provider in devices["value"]:
            for machine in provider["targets"]:
                if machine["id"][:4] != "ionq":
                    devices_dict[machine["id"]] = {
                        "status": machine["currentAvailability"],
                        "isAvailable": machine["currentAvailability"] == "Available",
                        "nextAvailable": None,
                        "availablilityCD": "",
                        "averageQueueTime": machine["averageQueueTime"],
                    }

        return devices_dict

    @staticmethod
    def create_container(
        token: str,
        subscription_id: str,
        resource_group_name: str,
        storage_account_name: str,
        session: Any,
    ) -> list[str]:
        """Create a new container for the job."""
        storage_access_token = token

        # NOTE: This step can be replaced with any code that qBraid has to generate job IDs,
        # but even the official Azure documentation uses UUIDs for job IDs

        job_id = str(uuid4())
        container_name = f"job-{job_id}"  # name of the container to create

        container_headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {storage_access_token}",
        }

        url = (
            f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/"
            f"{resource_group_name}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"  # pylint: disable=line-too-long
            f"/blobServices/default/containers/{container_name}?api-version=2022-09-01"
        )

        session.put(url, json={}, headers=container_headers)
        return [job_id, container_name]

    # pylint: disable=too-many-arguments
    @staticmethod
    def create_job_routes(
        session: str,
        container: str,
        qasm: str,
        connection_string: str,
        location_name: str,
        subscription_id: str,
        resource_group_name: str,
        workspace_name: str,
        quantum_access_token: str,
    ) -> list[str]:
        """Create the routes for the job."""
        containerName = container
        qasm_str = qasm

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        blob_client = blob_service_client.get_blob_client(containerName, "inputData")
        blob_client.upload_blob(
            qasm_str, content_settings=ContentSettings(content_type="application/qasm")
        )

        blob_client = blob_service_client.get_blob_client(containerName, "rawOutputData")
        blob_client.upload_blob("")

        url = (
            f"https://{location_name}.quantum.azure.com/subscriptions/{subscription_id}"
            f"/resourceGroups/{resource_group_name}/providers/Microsoft.Quantum/workspaces/"
            f"{workspace_name}/storage/sasUri?api-version=2022-09-12-preview"
        )

        quantum_headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {quantum_access_token}",
        }

        payload = {"containerName": containerName}

        response = session.post(url, json=payload, headers=quantum_headers)
        containerSasUri = response.json()["sasUri"]

        payload["blobName"] = "inputData"
        response = session.post(url, json=payload, headers=quantum_headers)
        inputSasUri = response.json()["sasUri"]

        payload["blobName"] = "rawOutputData"
        response = session.post(url, json=payload, headers=quantum_headers)
        outputSasUri = response.json()["sasUri"]

        return [containerSasUri, inputSasUri, outputSasUri, quantum_headers]

    # pylint: disable=too-many-arguments
    @staticmethod
    def create_payload(
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

    # pylint: disable=too-many-arguments
    @staticmethod
    def submit_job(
        job_id: str,
        payload: dict,
        job_header: dict,
        location_name: str,
        subscription_id: str,
        resource_group_name: str,
        workspace_name: str,
        session: Any,
    ) -> dict:
        """Submit the job to the Azure Quantum API."""
        url = (
            f"https://{location_name}.quantum.azure.com/subscriptions/{subscription_id}"
            f"/resourceGroups/{resource_group_name}/providers/Microsoft.Quantum/workspaces/"
            f"{workspace_name}/jobs/{job_id}?api-version=2022-09-12-preview"
        )

        response = session.put(url, json=payload, headers=job_header)
        return response.json()

    @staticmethod
    def get_output_data(container_name: str, connection_string: str) -> dict[str, Any]:
        """Get the output data from the job."""
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client("rawOutputData")
        blob_data = blob_client.download_blob().readall().decode("utf-8")

        return blob_data
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
Module defining Azure Session class for all Azure Quantum API calls.

"""
import re
from enum import Enum
from typing import IO, Any, AnyStr, Iterable, Optional, Union
from uuid import uuid4

import requests
from azure.identity import ClientSecretCredential
from azure.quantum import Workspace
from azure.storage.blob import BlobServiceClient, ContainerProperties, ContentSettings
from qbraid_core.exceptions import RequestsApiError

from qbraid.runtime.exceptions import ResourceNotFoundError


class ResourceScope(Enum):
    """Scope identifiers for different Microsoft Azure resources

    Attributes:
        QUANTUM (str): The scope for the Azure Quantum API.
        MANAGEMENT (str): The scope for the Azure Management API.

    """

    QUANTUM = "https://quantum.microsoft.com/.default"
    MANAGEMENT = "https://management.azure.com/.default"


class AzureSession(requests.Session):
    """Class for managing Azure Quantum API calls."""

    def __init__(self, credential: ClientSecretCredential, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._credential = credential

    @property
    def credential(self) -> ClientSecretCredential:
        """Get the authentication data for the Azure Quantum API."""
        return self._credential

    def get_access_token(self, scope: ResourceScope) -> str:
        """Function to get the access token for the Azure Quantum API."""
        url = f"https://login.microsoftonline.com/{self.credential._tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.credential._client_id,
            "client_secret": self.credential._client_credential,
            "scope": scope.value,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = super().post(url, headers=headers, data=data, verify=True)
        return response.json()["access_token"]

    def get_auth_headers(self, scope: ResourceScope) -> dict[str, str]:
        """Function to get the authorization headers for the Azure Quantum API."""
        token = self.get_access_token(scope)
        return {
            "Content-type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def _get_scope(self, url: str) -> ResourceScope:
        """Determines the scope based on the URL by matching against
        known Azure Quantum service requests pattern."""
        quantum_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.quantum\.azure\.com.*")

        if quantum_pattern.match(url):
            return ResourceScope.QUANTUM
        return ResourceScope.MANAGEMENT

    def _get_api_version(self, scope: ResourceScope) -> str:
        """Returns the API version based on the scope."""
        if scope == ResourceScope.QUANTUM:
            return "2022-09-12-preview"
        return "2022-09-01"

    def _request_with_auth(
        self,
        method: str,
        url: str,
        headers: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> requests.Response:
        """Helper method to send requests with updated authentication headers.

        Args:
            method (str): The HTTP method to use for the request.
            url (str): The URL to which the request is sent.
            headers (Optional[dict[str, Any]]): Additional headers to be sent with the request.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            requests.Response: The response object from the requests library.

        Raises:
            qbraid_core.RequestsApiError: If the response status code indicates an error.
        """
        headers = headers or {}
        scope = self._get_scope(url)
        headers.update(self.get_auth_headers(scope))

        params = kwargs.pop("params", {})
        params["api-version"] = self._get_api_version(scope)
        kwargs["params"] = params

        try:
            response = super().request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
        except requests.RequestException as error:
            raise RequestsApiError from error

        return response

    def get(self, url: str, **kwargs) -> requests.Response:
        return self._request_with_auth("GET", url, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Union[dict, list[tuple], bytes, IO]] = None,
        json: Optional[dict] = None,
        **kwargs,
    ) -> requests.Response:
        return self._request_with_auth("POST", url, data=data, json=json, **kwargs)

    def put(
        self, url: str, data: Optional[Union[dict, list[tuple], bytes, IO]] = None, **kwargs
    ) -> requests.Response:
        return self._request_with_auth("PUT", url, data=data, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        return self._request_with_auth("DELETE", url, **kwargs)


class AzureClient:
    """
    Manages interactions with Azure Quantum services, encapsulating API calls,
    and handling Azure Storage and session management.

    Attributes:
        workspace (Workspace): The configured Azure Quantum workspace.
        service (BlobServiceClient): Client for Azure Blob Storage service.
        session (AzureSession): Session object managing HTTP requests.
        storage_account (str): Name of the Azure storage account being used.
    """

    def __init__(self, workspace: Workspace, service: BlobServiceClient, session: AzureSession):
        """
        Initializes an AzureClient instance with specified Workspace, BlobServiceClient, and session.

        Args:
            workspace (Workspace): An initialized Azure Quantum Workspace object.
            service (BlobServiceClient): An initialized BlobServiceClient for interacting with Azure Blob Storage.
            session (AzureSession): A session object for managing authentication to Azure services.
        """
        self._workspace = workspace
        self._service = service
        self._session = session
        self._storage_account = self._get_storage_account(service)

    @classmethod
    def from_workspace(
        cls, workspace: Workspace, credential: Optional[ClientSecretCredential] = None
    ) -> "AzureClient":
        """
        Class method to instantiate an AzureClient based on a Workspace object, optionally with an
        explicit credential if the Workspace does not already include one.

        Args:
            workspace (Workspace): The Azure Quantum workspace object, potentially lacking a credential.
            credential (Optional[ClientSecretCredential]): Optional Azure ID credential to authenticate requests.

        Returns:
            AzureClient: An instance of AzureClient configured with the provided workspace and credentials.

        Raises:
            ValueError: If the workspace does not have a storage account specified, which is required for operations.
        """
        if workspace.credential is None and credential:
            workspace.credential = credential

        if workspace.storage is None:
            raise ValueError("Workspace must have a storage account specified.")

        service = BlobServiceClient.from_connection_string(
            workspace.storage, credential=workspace.credential
        )
        session = AzureSession(credential)
        return cls(workspace, service, session)

    @property
    def workspace(self) -> Workspace:
        """Get the Azure Quantum workspace."""
        return self._workspace

    @property
    def service(self) -> BlobServiceClient:
        """Get the Azure Blob Service client."""
        return self._service

    @property
    def session(self) -> AzureSession:
        """Get the authentication data for the Azure Quantum API."""
        return self._session

    @property
    def storage_account(self) -> str:
        """Get the storage account name for the Azure Quantum workspace."""
        return self._storage_account

    @staticmethod
    def _get_storage_account(service: BlobServiceClient) -> str:
        """Parse the storage account name from a blob service client's URL."""
        account_url: str = service.url
        account_name = account_url.split(".")[0].split("//")[1]
        return account_name

    def _construct_request_url(self, route: str, scope: ResourceScope) -> str:
        """Constructs a URL for an Azure Quantum API request."""
        base_url = (
            f"https://{self.workspace.location}.quantum.azure.com/"
            if scope == ResourceScope.QUANTUM
            else "https://management.azure.com/"
        )

        shared_path = (
            f"subscriptions/{self.workspace.subscription_id}/"
            f"resourceGroups/{self.workspace.resource_group}/"
        )

        specific_path = (
            f"providers/Microsoft.Quantum/workspaces/{self.workspace.name}"
            if scope == ResourceScope.QUANTUM
            else f"providers/Microsoft.Storage/storageAccounts/{self._storage_account}"
        )

        route = "/" + route.lstrip("/")
        return f"{base_url}{shared_path}{specific_path}{route}"

    def get_devices(
        self, providers: Optional[list[str]] = None, statuses: Optional[list[str]] = None
    ) -> dict[str, dict[str, Any]]:
        """Retrieves a dictionary of devices from the Azure Quantum API.

        Each key in the returned dictionary is a device ID, and the value is a dictionary
        of properties for that device.

        Args:
            providers (Optional[list[str]]): List of provider IDs to filter the devices by.
            statuses (Optional[list[str]]): List of statuses to filter the devices by.

        Returns:
            dict[str, dict[str, Any]]: A dictionary mapping device IDs to their properties.
        """
        url = self._construct_request_url("/providerStatus", ResourceScope.QUANTUM)

        response = self.session.get(url)
        response_data: dict[str, Any] = response.json()
        provider_data: list[dict[str, Any]] = response_data.get("value", [])

        if providers is not None:
            provider_data = [p for p in provider_data if p.get("id") in set(providers)]

        device_data: list[dict[str, Any]] = [t for p in provider_data for t in p.get("targets", [])]
        if statuses is not None:
            device_data = [d for d in device_data if d.get("currentAvailability") in set(statuses)]

        try:
            devices = {device["id"]: device for device in device_data}
        except KeyError as err:
            raise RuntimeError("Failed to parse device data") from err

        return devices

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Retrieves the properties of a specific device from the Azure Quantum API.

        Args:
            device_id (str): The ID of the device to retrieve.

        Returns:
            dict[str, Any]: A dictionary of properties for the specified device.

        """
        devices = self.get_devices()
        device = devices.get(device_id)
        if device is None:
            raise ResourceNotFoundError(f"Device {device_id} not found.")
        return device

    def create_container(self, name: Optional[str] = None) -> dict[str, str]:
        """Creates a new container for the Azure Quantum API.

        Args:
            name (Optional[str]): The name of the container to create. If not provided,
                a random name will be generated.

        Returns:
            dict[str, str]: A dictionary containing the container ID and name.
        """
        container_name = name or f"job-{uuid4()}"
        route = f"/blobServices/default/containers/{container_name}"
        url = self._construct_request_url(route, ResourceScope.MANAGEMENT)
        response = self.session.put(url, json={})
        return response.json()

    def upload_blob(
        self,
        container: Union[ContainerProperties, str],
        blob: str,
        data: Union[bytes, str, Iterable[AnyStr], IO[bytes]],
        content_settings: Optional[ContentSettings] = None,
    ) -> None:
        """
        Uploads a blob to Azure Blob Storage and retrieves a SAS URI for the blob.

        Args:
            container (Union[ContainerProperties, str]): Container where the blob will be stored.
            blob (str): Name of the blob (file) to create and upload data into.
            data (Union[bytes, str, Iterable[AnyStr], IO[bytes]]): Content to upload into the blob.
            content_settings (Optional[ContentSettings]): Content settings to apply to the blob.
        """
        blob_client = self.service.get_blob_client(container, blob)
        blob_client.upload_blob(data, content_settings=content_settings)

    def generate_sas_uri(
        self, container: Union[ContainerProperties, str], blob: Optional[str] = None
    ) -> str:
        """
        Retrieves a Shared Access Signature (SAS) URI for a specified container or blob.

        Args:
            container (Union[ContainerProperties, str]): The container's properties object or name.
            blob (Optional[str]): Optional name of a blob within the container. If provided,
                generates a SAS URI for this blob; otherwise, for the container.

        Returns:
            str: The SAS URI providing access under the current access policy.

        """
        container_name = container.name if isinstance(container, ContainerProperties) else container

        payload = {"containerName": container_name}

        if blob is not None:
            payload["blobName"] = blob

        url = self._construct_request_url("/storage/sasUri", ResourceScope.QUANTUM)
        response = self.session.post(url, json=payload)
        return response.json()["sasUri"]

    def create_job_storage(
        self, data: Union[bytes, str, Iterable[AnyStr], IO[bytes]], content_type: str
    ) -> dict[str, Any]:
        """
        Initializes storage for a job, uploads input data, and generates SAS URIs
        for the container and blobs.

        Args:
            data (Union[bytes, str, Iterable[AnyStr], IO[bytes]]): The input data to be uploaded.
            content_type (str): MIME type for setting the content settings of the input data blob.

        Returns:
            dict[str, Any]: A dictionary containing the container ID and SAS URIs for the container,
                input, and output data.

        """
        container_data = self.create_container()
        container_name = container_data["name"]

        blob_input_data = "inputData"
        blob_output_data = "rawOutputData"
        content_settings = ContentSettings(content_type=content_type)
        self.upload_blob(container_name, blob_input_data, data, content_settings=content_settings)
        self.upload_blob(container_name, blob_output_data, "", content_settings=None)

        container_uri = self.generate_sas_uri(container_name)
        input_data_uri = self.generate_sas_uri(container_name, blob_input_data)
        output_data_uri = self.generate_sas_uri(container_name, blob_output_data)

        storage_data = {
            "id": container_name,
            "containerUri": container_uri,
            "inputDataUri": input_data_uri,
            "outputDataUri": output_data_uri,
        }

        return storage_data

    def submit_job(self, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Submits a job to the Azure Quantum API.

        Args:
            job_id (str): The ID of the job to submit.
            payload (dict[str, Any]): The payload containing job information.

        Returns:
            dict[str, Any]: A dictionary containing information about the submitted job.

        """
        url = self._construct_request_url(f"/jobs/{job_id}", ResourceScope.QUANTUM)
        response = self.session.put(url, json=payload)
        return response.json()

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Retrieves information about a specific job from the Azure Quantum API.

        Args:
            job_id (str): The ID of the job to retrieve information about.

        Returns:
            dict[str, Any]: A dictionary containing information about the specified job.
        """
        url = self._construct_request_url(f"/jobs/{job_id}", ResourceScope.QUANTUM)
        response = self.session.get(url)
        return response.json()

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """Cancels a job in the Azure Quantum API.

        Args:
            job_id (str): The ID of the job to cancel.

        Returns:
            dict[str, Any]: A dictionary containing information about the cancelled job.
        """
        url = self._construct_request_url(f"/jobs/{job_id}", ResourceScope.QUANTUM)
        response = self.session.delete(url)
        return response.json()

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
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from qbraid_core.sessions import Session

if TYPE_CHECKING:
    import requests


class ResourceScope(Enum):
    """Scope identifiers for different Microsoft Azure resources

    Attributes:
        QUANTUM (str): The scope for the Azure Quantum API.
        MANAGEMENT (str): The scope for the Azure Management API.

    """

    QUANTUM = "https://quantum.microsoft.com/.default"
    MANAGEMENT = "https://management.azure.com/.default"


@dataclass(frozen=True)
class AuthData:
    """
    Dataclass for storing the authentication data
    for the Azure Quantum API.

    Attributes:
        client_id (str): The client ID for the Azure Quantum API.
        client_secret (str): The client secret for the Azure Quantum API.
        tenant_id (str): The tenant ID for the Azure Quantum API.
        location_name (str): The location name for the Azure Quantum API.
        subscription_id (str): The subscription ID for the Azure Quantum API.
        resource_group (str): The resource group for the Azure Quantum API.
        workspace_name (str): The workspace name for the Azure Quantum API.
        storage_account (str): The storage account for the Azure Quantum API.
        api_connection (str): The API connection for the Azure Quantum API.

    """

    client_id: str
    client_secret: str
    tenant_id: str
    location_name: str
    subscription_id: str
    resource_group: str
    workspace_name: str
    storage_account: str
    api_connection: str


class AzureSession(Session):
    """Class for managing Azure Quantum API calls."""

    def __init__(self, auth_data: AuthData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._auth_data = auth_data
        self.api_version = "2022-09-12-preview"

    @property
    def auth_data(self) -> AuthData:
        """Get the authentication data for the Azure Quantum API."""
        return self._auth_data

    def get_access_token(self, scope: ResourceScope) -> str:
        """Function to get the access token for the Azure Quantum API."""
        url = f"https://login.microsoftonline.com/{self.auth_data.tenant_id}/oauth2/v2.0/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": self.auth_data.client_id,
            "client_secret": self.auth_data.client_secret,
            "scope": scope.value,
        }

        static_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = super().post(url, headers=static_headers, data=data, verify=True)
        return response.json()["access_token"]

    def get_auth_headers(self, header_type: ResourceScope) -> dict:
        """Function to get the authorization headers for the Azure Quantum API."""
        token = self.get_access_token(header_type)

        auth_header = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        return auth_header

    def get(self, url: str) -> "requests.Response":
        """Function to make a GET request to the Azure Quantum API."""
        quantum_headers = self.get_auth_headers(ResourceScope.QUANTUM)
        return super().get(url, headers=quantum_headers)

    def put(self, url: str, payload: dict, put_type: ResourceScope) -> "requests.Response":
        """Function to make a PUT request to the Azure Quantum API."""
        auth_headers = self.get_auth_headers(put_type)
        return super().put(url, json=payload, headers=auth_headers)

    def post(self, payload: dict) -> "requests.Response":
        """Function to make a POST request to the Azure Quantum API."""
        url = (
            f"https://{self.auth_data.location_name}.quantum.azure.com/"
            f"subscriptions/{self.auth_data.subscription_id}/"
            f"resourceGroups/{self.auth_data.resource_group}/"
            f"providers/Microsoft.Quantum/workspaces/"
            f"{self.auth_data.workspace_name}/storage/sasUri"
            f"?api-version={self.api_version}"
        )

        auth_headers = self.get_auth_headers(ResourceScope.QUANTUM)
        return super().post(url, json=payload, headers=auth_headers)

    def delete(self, job: str) -> "requests.Response":
        """Function to make a DELETE request to the Azure Quantum API."""
        url = (
            f"https://{self.auth_data.location_name}.quantum.azure.com/"
            f"subscriptions/{self.auth_data.subscription_id}/"
            f"resourceGroups/{self.auth_data.resource_group}/"
            f"providers/Microsoft.Quantum/"
            f"workspaces/{self.auth_data.workspace_name}/jobs/{job}"
            f"?api-version={self.api_version}"
        )
        quantum_headers = self.get_auth_headers(ResourceScope.QUANTUM)

        return super().delete(url, headers=quantum_headers)

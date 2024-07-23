# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=line-too-long
# pylint: disable=arguments-differ

"""
Module defining Azure Session class for all Azure Quantum API calls.

"""

from typing import Any

from qbraid_core.sessions import Session


class AzureSession(Session):
    """Class for managing Azure Quantum API calls."""

    def __init__(self, auth_data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client_id = auth_data["client_id"]
        self.client_secret = auth_data["client_secret"]
        self.tenant_id = auth_data["tenant_id"]
        self.location_name = auth_data["location_name"]
        self.subscription_id = auth_data["subscription_id"]
        self.resource_group = auth_data["resource_group"]
        self.workspace_name = auth_data["workspace_name"]
        self.storage_account = auth_data["storage_account"]
        self.api_connection = auth_data["api_connection"]

        self.static_headers = {"Content-Type": "application/x-www-form-urlencoded"}

    def get_access_token(self, token_type: str) -> str:
        """Function to get the access token for the Azure Quantum API."""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": (
                "https://quantum.microsoft.com/.default"
                if token_type == "quantum"
                else "https://management.azure.com/.default"
            ),
        }

        response = super().post(url, headers=self.static_headers, data=data, verify=True)
        return response.json()["access_token"]

    def get_auth_headers(self, header_type: str) -> dict:
        """Function to get the authorization headers for the Azure Quantum API."""
        auth_header = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.get_access_token(header_type)}",
        }

        return auth_header

    def get(self, url: str) -> Any:
        """Function to make a GET request to the Azure Quantum API."""
        quantum_headers = self.get_auth_headers("quantum")
        return super().get(url, headers=quantum_headers)

    def put(self, url: str, payload: dict, put_type: str) -> Any:
        """Function to make a PUT request to the Azure Quantum API."""
        auth_headers = self.get_auth_headers(put_type)
        return super().put(url, json=payload, headers=auth_headers)

    def post(self, payload: dict) -> Any:
        """Function to make a POST request to the Azure Quantum API."""
        url = (
            f"https://{self.location_name}.quantum.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}/providers/Microsoft.Quantum/workspaces/"
            f"{self.workspace_name}/storage/sasUri?api-version=2022-09-12-preview"
        )

        auth_headers = self.get_auth_headers("quantum")
        return super().post(url, json=payload, headers=auth_headers)

    # pylint: disable=arguments-renamed
    def delete(self, job: str) -> Any:
        """Function to make a DELETE request to the Azure Quantum API."""
        url = (
            f"https://{self.location_name}.quantum.azure.com/subscriptions/"
            f"{self.subscription_id}/resourceGroups/{self.resource_group}/"
            f"providers/Microsoft.Quantum/workspaces/{self.workspace_name}/jobs/"
            f"{job}?api-version=2022-09-12-preview"
        )
        quantum_headers = self.get_auth_headers("quantum")

        return super().delete(url, headers=quantum_headers)

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
from typing import Any, Optional

from azure.identity import ClientSecretCredential
from azure.quantum import Workspace
from azure.quantum.job import Job

from qbraid.runtime.exceptions import ResourceNotFoundError


class AzureClient:
    """
    Manages interactions with Azure Quantum services, encapsulating API calls,
    and handling Azure Storage and session management.

    Attributes:
        workspace (Workspace): The configured Azure Quantum workspace.
    """

    def __init__(self, workspace: Workspace):
        """
        Initializes an AzureClient instance with specified Workspace.

        Args:
            workspace (Workspace): An initialized Azure Quantum Workspace object.
        """
        self._workspace = workspace

    @classmethod
    def from_workspace(
        cls, workspace: Workspace, credential: Optional[ClientSecretCredential] = None
    ) -> "AzureClient":
        """
        Class method to instantiate an AzureClient based on a Workspace object, optionally with an
        explicit credential if the Workspace does not already include one.

        Args:
            workspace (Workspace): Azure Quantum workspace object, potentially lacking credential.
            credential (Optional[ClientSecretCredential]): Optional Azure ID credential.

        Returns:
            AzureClient: Instance of AzureClient configured with provided workspace and credentials.
        """
        if workspace.credential is None and credential:
            workspace.credential = credential

        return cls(workspace)

    @property
    def workspace(self) -> Workspace:
        """Get the Azure Quantum workspace."""
        return self._workspace

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
        device_dict = {
            device.name: {
                "input_data_format": device.input_data_format,
                "output_data_format": device.output_data_format,
                "capability": device.capability,
                "provider_id": device.provider_id,
                "content_type": device.content_type,
                "_average_queue_time": device._average_queue_time,
                "_current_availability": device._current_availability,
            }
            for device in self._workspace.get_targets()
            if (providers is None or device.provider_id in providers)
            and (statuses is None or device._current_availability in statuses)
        }

        return device_dict

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

        device["name"] = device_id
        return device

    def submit_job(self, data_dict: dict) -> Job:
        """Submits a job to the Azure Quantum API.

        Args:
            data_dict (dict): A dictionary containing the device name, program,
            name, and shots for the job.

        Returns:
            dict[str, Any]: A dictionary containing information about the submitted job.

        """
        device_name, program, job_name, shots = (
            data_dict["device_name"],
            data_dict["program"],
            data_dict["job_name"],
            data_dict["shots"],
        )

        target = self._workspace.get_targets(device_name)
        job = target.submit(input_data=program, name=job_name, shots=shots)
        return job

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Retrieves information about a specific job from the Azure Quantum API.

        Args:
            job_id (str): The ID of the job to retrieve information about.

        Returns:
            dict[str, Any]: A dictionary containing information about the specified job.
        """
        return self._workspace.get_job(job_id)

    def get_job_results(self, job: Job) -> dict[str, Any]:
        """Retrieves information about a specific job from the Azure Quantum API.

        Args:
            job_id (str): The ID of the job to retrieve information about.

        Returns:
            dict[str, Any]: A dictionary containing information about the specified job.
        """
        return job.get_results()

    def cancel_job(self, job: Job) -> None:
        """Cancels a job in the Azure Quantum API.

        Args:
            job_id (str): The ID of the job to cancel.
        """
        self._workspace.cancel_job(job)

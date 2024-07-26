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
Module defining Azure Provider class for retrieving all Azure backends.

"""
from qbraid.runtime.enums import DeviceType
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .client import AzureClient
from .device import AzureQuantumDevice


class AzureQuantumProvider(QuantumProvider):
    """Azure provider class."""

    def __init__(self, client: AzureClient):
        super().__init__()
        self._client = client

    @property
    def client(self) -> AzureClient:
        """Get the Azure client."""
        return self._client

    def _build_profile(self, data: str) -> TargetProfile:
        """Builds a profile for an Azure device.

        Args: data (str): The device data to build profile from.

        Returns: TargetProfile: The built profile.
        """
        device_id = data
        provider_name = device_id.split(".", 1)[0]
        is_qpu = device_id.split(".", 1)[1] == "qpu"
        device_type = DeviceType.QPU if is_qpu else DeviceType.SIMULATOR

        return TargetProfile(
            device_id=device_id,
            device_type=device_type,
            provider_name=provider_name,
        )

    def get_devices(self, **kwargs) -> list[AzureQuantumDevice]:
        """Get all Azure Quantum devices.

        Args: **kwargs: Additional keyword arguments.

        Returns: list[AzureQuantumDevice]: The list of Azure Quantum devices."""
        devices_map = self.client.get_devices(**kwargs)
        devices_data = list(devices_map.keys())
        return [
            AzureQuantumDevice(self._build_profile(device), self.client) for device in devices_data
        ]

    def get_device(self, device_id: str) -> AzureQuantumDevice:
        """Get a specific Azure Quantum device.

        Args: device_id (str): The ID of the device to retrieve.

        Returns: AzureQuantumDevice: The Azure Quantum device."""
        device_data = self.client.get_device(device_id)
        if device_data is None:
            raise ValueError(f"Device {device_id} not found.")
        return AzureQuantumDevice(self._build_profile(device_data["name"]), self.client)

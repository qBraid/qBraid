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

from typing import Any

import openqasm3
from qbraid_core._import import LazyLoader

from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.enums import DeviceType
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import AzureQuantumDevice
from .session import AuthData, AzureSession

pyquil = LazyLoader("pyquil", globals(), "pyquil")


class AzureQuantumProvider(QuantumProvider):
    """Azure provider class."""

    def __init__(self, auth_data: AuthData):
        super().__init__()
        self.session = AzureSession(auth_data)

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

    def get_devices(self) -> list[dict[str, Any]]:
        """Get all Azure Quantum devices."""
        auth_data = self.session.auth_data

        url = (
            f"https://{auth_data.location_name}.quantum.azure.com/"
            f"subscriptions/{auth_data.subscription_id}/"
            f"resourceGroups/{auth_data.resource_group}/"
            f"providers/Microsoft.Quantum/"
            f"workspaces/{auth_data.workspace_name}/"
            f"providerStatus?api-version=2022-09-12-preview"
        )

        r = self.session.get(url)
        devices = r.json()

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

        all_devices = [{"id": k, **v} for k, v in devices_dict.items()]

        quantum_devices = [
            AzureQuantumDevice(self._build_profile(device), self.session) for device in all_devices
        ]

        return [quantum_devices, all_devices]

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Get a specific Azure Quantum device."""
        devices = self.get_devices()

        for i in devices[1]:
            if i.get("id") == device_id:
                profile = self._build_profile(i)
                return AzureQuantumDevice(profile, self.session)

        raise AttributeError(f"Device {device_id} not found.")

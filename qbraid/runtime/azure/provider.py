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

from qbraid_core.sessions import Session

from qbraid.runtime.enums import DeviceType
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import AzureQuantumDevice


class AzureSession(Session):
    """Azure session class."""

    # NOTE: The below initialization outline is simply an outline, and does not represent a correct implementation.
    # Because of the fact that Azure uses two step authentication, we cannot assume that the user already has the
    # access token. So this initialization will intead most likely need to ask the user for the client ID and client
    # secret so that we can then programmatically retrieve the access token, and form the authorization header.

    def __init__(self, access_token: str, location_name: str):
        super().__init__(
            base_url=f"https://{location_name}.quantum.azure.com",
            headers={"Content-Type": "application/json"},
            auth_headers={"Authorization": f"Bearer {access_token}"},
        )

    def get_devices(self, **kwargs) -> dict[str, dict[str, Any]]:
        """Get all Azure Quantum devices."""
        raise NotImplementedError

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Get a specific Azure Quantum device."""
        raise NotImplementedError

    def create_job(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new job on the Azure Quantum API."""
        raise NotImplementedError

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Get a specific Azure Quantum job."""
        raise NotImplementedError

    def cancel_job(self, job_id: str):
        """Cancel a specific Azure Quantum job."""
        raise NotImplementedError


class AzureQuantumProvider(QuantumProvider):
    """Azure provider class."""

    def __init__(self, access_token: str, location_name: str):
        super().__init__()
        self.session = AzureSession(access_token, location_name)

    def _build_profile(self, data: dict[str, Any]) -> TargetProfile:
        """Build a profile for an Azure device."""
        return TargetProfile(
            device_id=data.get("backend"),
            device_type=DeviceType.QPU,
            num_qubits=data.get("qubits"),
            program_spec=None,  # TODO: Add program spec
        )

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Get a specific Azure device."""
        data = self.session.get_device(device_id)
        profile = self._build_profile(data)
        return AzureQuantumDevice(profile, self.session)

    def get_devices(self, **kwargs) -> list[AzureQuantumDevice]:
        """Get a list of Azure devices."""
        devices = self.session.get_devices(**kwargs)
        return [
            AzureQuantumDevice(self._build_profile(device), self.session)
            for device in devices.values()
        ]

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
Module defining OQC provider class

"""
from typing import Any

from qcaas_client.client import OQCClient

from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.enums import DeviceType
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import OQCDevice


class OQCProvider(QuantumProvider):
    """OQC provider class."""

    def __init__(self, api_key: str):
        super().__init__()
        self.client = OQCClient(url="https://cloud.oqc.app/", authentication_token=api_key)

    def _build_profile(self, data: dict[str, Any]) -> TargetProfile:
        """Build a profile for OQC device."""
        return TargetProfile(
            device_id=data["id"],
            device_type=DeviceType.SIMULATOR,
            num_qubits=data["num_qubits"],
            program_spec=ProgramSpec(str, alias="qasm2"),
        )

    def get_devices(self, **kwargs) -> list[OQCDevice]:
        """Get all OQC devices."""
        devices = self.client.get_qpus()
        data = [
            {"id": device["id"], "num_qubits": 8} for device in devices
        ]  # TODO: Dynamically get num_qubits
        return [OQCDevice(profile=self._build_profile(x), client=self.client) for x in data]

    def get_device(self, device_id: str) -> OQCDevice:
        """Get a specific OQC device."""
        devices = self.get_devices()
        for device in devices:
            if device.profile._data["device_id"] == device_id:
                return device
        raise ResourceNotFoundError(f"Device '{device_id}' not found.")

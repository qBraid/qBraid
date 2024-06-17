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
Module defining Oxford Quantum Circuits (OQC) provider class

"""
from typing import Any

from qcaas_client.client import OQCClient

from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.enums import DeviceActionType, DeviceType
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import OQCDevice


class OQCProvider(QuantumProvider):
    """OQC provider class."""

    def __init__(self, token: str):
        super().__init__()
        self.client = OQCClient(url="https://cloud.oqc.app/", authentication_token=token)

    def _build_profile(self, data: dict[str, Any]) -> TargetProfile:
        """Build a profile for OQC device."""
        # TODO: dynamically get the number of qubits of device endpoint url.
        qpu_num_qubits = {"qpu:uk:2:d865b5a184": 8}

        device_id: str = data["id"]
        device_name: str = data["name"]
        device_type = DeviceType.SIMULATOR if "simulator" in device_name.lower() else DeviceType.QPU

        return TargetProfile(
            device_id=device_id,
            device_type=device_type,
            action_type=DeviceActionType.OPENQASM,
            num_qubits=qpu_num_qubits.get(device_id),
            program_spec=ProgramSpec(str, alias="qasm2"),
            device_name=device_name,
            endpoint_url=data["url"],
            provider_name="Oxford",
        )

    def get_devices(self, **kwargs) -> list[OQCDevice]:
        """Get all OQC devices."""
        devices: list[dict] = self.client.get_qpus()
        return [
            OQCDevice(profile=self._build_profile(device), client=self.client) for device in devices
        ]

    def get_device(self, device_id: str) -> OQCDevice:
        """Get a specific OQC device."""
        devices: list[dict] = self.client.get_qpus()
        for device in devices:
            if device["id"] == device_id:
                return OQCDevice(profile=self._build_profile(device), client=self.client)
        raise ResourceNotFoundError(f"Device '{device_id}' not found.")

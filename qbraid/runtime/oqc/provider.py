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

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType
from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import OQCDevice


class OQCProvider(QuantumProvider):
    """OQC provider class."""

    def __init__(self, token: str):
        self.client = OQCClient(url="https://cloud.oqc.app/", authentication_token=token)

    def _build_profile(self, data: dict[str, Any]) -> TargetProfile:
        """Build a profile for OQC device."""
        data = OQCDevice._decode_feature_set(data)

        try:
            device_id: str = data["id"]
            device_name: str = data["name"]
            endpoint_url: str = data["url"]
            simulator: bool = data["feature_set"]["simulator"]
            num_qubits: int = data["feature_set"]["qubit_count"]
        except KeyError as err:
            raise ValueError(
                f"Failed to gather profile data for device '{data.get('id')}'."
            ) from err

        return TargetProfile(
            device_id=device_id,
            simulator=simulator,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=num_qubits,
            program_spec=ProgramSpec(str, alias="qasm3"),
            device_name=device_name,
            endpoint_url=endpoint_url,
            provider_name="OQC",
        )

    @cached_method
    def get_devices(self) -> list[OQCDevice]:
        """Get all OQC devices."""
        devices: list[dict] = self.client.get_qpus()
        return [
            OQCDevice(profile=self._build_profile(device), client=self.client) for device in devices
        ]

    @cached_method
    def get_device(self, device_id: str) -> OQCDevice:
        """Get a specific OQC device."""
        devices: list[dict] = self.client.get_qpus()
        for device in devices:
            if device["id"] == device_id:
                return OQCDevice(profile=self._build_profile(device), client=self.client)
        raise ResourceNotFoundError(f"Device '{device_id}' not found.")

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(
                self, "_hash", hash((self.client.url, self.client._authentication_token))
            )
        return self._hash  # pylint: disable=no-member

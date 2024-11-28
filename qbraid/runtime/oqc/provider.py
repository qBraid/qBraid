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
import json
import os
from typing import Any, Optional, Union

from qcaas_client.client import OQCClient

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType
from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider
from qbraid.runtime.schemas.base import USD

from .device import OQCDevice

NATIVE_GATES = {"qpu:jp:3:673b1ad43c": {"ecr", "id", "rz", "sx", "x"}}


class OQCProvider(QuantumProvider):
    """OQC provider class."""

    def __init__(
        self,
        token: Optional[str] = None,
        url: str = "https://cloud.oqc.app/",
        timeout: tuple[int, int] = (5, 10),
    ) -> None:
        token = token or os.getenv("OQC_AUTH_TOKEN")
        if not token:
            raise ValueError(
                "An OQC authenication token is required to initialize the provider. "
                "Please provide it directly as an argument or set it via "
                "the OQC_AUTH_TOKEN environment variable."
            )
        self.client = OQCClient(url=url, authentication_token=token, timeout=timeout)

    def _build_profile(self, data: dict[str, Any]) -> TargetProfile:
        """Build a profile for OQC device."""
        data = data.copy()
        device_id = data.get("id")
        feature_set: Union[str, dict] = data.get("feature_set", {})

        if not isinstance(feature_set, dict):
            try:
                data["feature_set"] = json.loads(feature_set)
            except json.JSONDecodeError as err:
                raise ValueError(
                    f"Failed to decode feature set data for device '{device_id}'."
                ) from err

        try:
            device_id: str = data.pop("id")
            device_name: str = data.pop("name")
            endpoint_url: str = data.pop("url")
            feauture_set: dict = data.pop("feature_set")
            num_qubits: int = feauture_set.pop("qubit_count")
            simulator: bool = feauture_set.pop("simulator", False)
        except KeyError as err:
            raise ValueError(f"Failed to gather profile data for device '{device_id}'.") from err

        dynamic_fields = {"active", "status"}
        pricing_fields = {"price_per_shot", "price_per_task"}
        static_data = {
            k: (USD(v) if k in pricing_fields else v)
            for k, v in data.items()
            if k not in dynamic_fields
        }

        return TargetProfile(
            device_id=device_id,
            simulator=simulator,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=num_qubits,
            program_spec=ProgramSpec(str, alias="qasm3"),
            device_name=device_name,
            endpoint_url=endpoint_url,
            provider_name="OQC",
            feature_set=feauture_set,
            **static_data,
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
        device = next((d for d in devices if d["id"] == device_id), None)
        if not device:
            raise ResourceNotFoundError(f"Device '{device_id}' not found.")
        return OQCDevice(profile=self._build_profile(device), client=self.client)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(
                self, "_hash", hash((self.client.url, self.client._authentication_token))
            )
        return self._hash  # pylint: disable=no-member

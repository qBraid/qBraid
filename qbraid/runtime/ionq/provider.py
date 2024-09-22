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
Module defining IonQ session and provider classes

"""
from typing import Any

from qbraid_core.sessions import Session

from qbraid._caching import cached_method
from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.enums import ExperimentType
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import IonQDevice

SUPPORTED_GATES = [
    "x",
    "y",
    "z",
    "rx",
    "ry",
    "rz",
    "h",
    "cx",
    "s",
    "sdg",
    "t",
    "tdg",
    "sx",
    "sxdg",
    "swap",
]


class IonQSession(Session):
    """IonQ session class."""

    def __init__(self, api_key: str):
        super().__init__(
            base_url="https://api.ionq.co/v0.3",
            headers={"Content-Type": "application/json"},
            auth_headers={"Authorization": f"apiKey {api_key}"},
        )
        self.api_key = api_key

    def get_devices(self, **kwargs) -> dict[str, dict[str, Any]]:
        """Get all IonQ devices."""
        devices_list = self.get("/backends", **kwargs).json()
        devices_dict = {device["backend"]: device for device in devices_list}
        return devices_dict

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Get a specific IonQ device."""
        devices = self.get_devices()
        return devices.get(device_id)

    def create_job(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new job on the IonQ API."""
        return self.post("/jobs", data=data).json()

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Get a specific IonQ job."""
        return self.get(f"/jobs/{job_id}").json()

    def cancel_job(self, job_id: str):
        """Cancel a specific IonQ job."""
        return self.put(f"/jobs/{job_id}/status/cancel").json()


class IonQProvider(QuantumProvider):
    """IonQ provider class."""

    def __init__(self, api_key: str):
        self.session = IonQSession(api_key)

    def _build_profile(self, data: dict[str, Any]) -> TargetProfile:
        """Build a profile for an IonQ device."""
        device_id = data.get("backend")
        simulator = device_id == "simulator"

        return TargetProfile(
            device_id=device_id,
            simulator=simulator,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=data.get("qubits"),
            program_spec=ProgramSpec(str, alias="qasm2"),
            provider_name="IonQ",
            basis_gates=SUPPORTED_GATES,
        )

    @cached_method
    def get_device(
        self,
        device_id: str,
    ) -> dict[str, Any]:
        """Get a specific IonQ device."""
        data = self.session.get_device(device_id)
        profile = self._build_profile(data)
        return IonQDevice(profile, self.session)

    @cached_method
    def get_devices(self, **kwargs) -> list[IonQDevice]:
        """Get a list of IonQ devices."""
        devices = self.session.get_devices(**kwargs)
        return [
            IonQDevice(self._build_profile(device), self.session) for device in devices.values()
        ]

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(self, "_hash", hash((self.session.api_key, self.session.base_url)))
        return self._hash  # pylint: disable=no-member

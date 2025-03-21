# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining QUDORA session and provider classes

"""

import os
from typing import Any, Optional

from qbraid_core.sessions import Session

from qbraid._caching import cached_method
from qbraid._version import __version__ as qbraid_version
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import QUDORABackend


class QUDORASession(Session):
    """QUDORA session class."""

    def __init__(
        self,
        token: Optional[str] = None,
        url: str = "https://api.qudora.com",
        timeout: Optional[int] = None,
    ):
        token = token or os.getenv("QUDORA_API_TOKEN")
        if not token:
            raise ValueError(
                "A QUDORA API token is required to initialize the session. "
                "Please provide it directly as an argument or set it via "
                "the QUDORA_API_TOKEN environment variable."
            )

        super().__init__(
            base_url=url,
            auth_headers={"Authorization": f"Bearer {token}"},
        )
        self.token = token
        self.timeout = timeout
        self.add_user_agent(f"QbraidSDK/{qbraid_version}")

    def get_devices(self, **filters) -> list[dict[str, Any]]:
        """Get all QUDORA devices."""
        devices: list[dict[str, Any]] = self.get("/backends/", timeout=self.timeout).json()

        if filters:
            devices = [
                device
                for device in devices
                if all(device.get(key) == value for key, value in filters.items())
            ]

        return devices

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Get a specific QUDORA device."""
        devices = self.get_devices()

        for device in devices:
            if device.get("username") == device_id or device.get("full_name") == device_id:
                return device

        raise ResourceNotFoundError(f"Device '{device_id}' not found.")

    def create_job(self, data: dict[str, Any]) -> int:
        """Posts a job to the QUDORA API and returns the job ID."""
        return self.post("/jobs/", data=data, timeout=self.timeout).json()

    def get_job(self, job_id: str, include_data: bool = True) -> dict[str, Any]:
        """Queries for a specific job from the QUDORA API.

        Args:
            include_data (bool, optional): Should job data (input,results,errors) be included.
                Defaults to True.

        Returns:
            dict[str, Any]: Data of the job.
        """
        return self.get(
            "/jobs/",
            params={
                "job_id": job_id,
                "include_results": include_data,
                "include_tiasm": False,
                "include_input_data": include_data,
                "include_user_error": include_data,
            },
            timeout=self.timeout,
        ).json()

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """Tries to cancel a specific QUDORA job."""
        return self.put(
            "/jobs/", params={"job_id": job_id, "status_name": "Canceled"}, timeout=self.timeout
        ).json()


class QUDORAProvider(QuantumProvider):
    """QUDORA provider class."""

    def __init__(self, token: Optional[str] = None):
        self.session = QUDORASession(token)

    def _build_profile(self, info: dict[str, Any]) -> TargetProfile:
        """Build a profile for an QUDORA device."""
        try:
            device_id: str = info["full_name"]
            username: str = info["username"]
            simulator: bool = info["simulator"]
            basis_gates: list[str] = info["basis_gates"]
            num_qubits: int = info["max_n_qubits"]
            max_shots: int = info["max_shots"]
            max_programs_per_job = info["max_programs_per_job"]
            user_settings_schema: dict = info.get("user_settings_schema", {})
            available_settings = user_settings_schema.get("properties", {})
        except KeyError as err:
            message = "Failed to gather profile data for device"
            alias: Optional[str] = info.get("full_name", info.get("username"))
            message += f" '{alias}'." if alias else "."
            err.add_note("Did not receive required information from the QUDORA Cloud API.")
            raise ValueError(message) from err

        return TargetProfile(
            device_id=device_id,
            simulator=simulator,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=num_qubits,
            program_spec=[
                ProgramSpec(str, alias="qasm2"),
                ProgramSpec(str, alias="qasm3"),
            ],
            provider_name="QUDORA",
            basis_gates=basis_gates,
            username=username,
            max_shots=max_shots,
            max_programs_per_job=max_programs_per_job,
            available_settings=available_settings,
        )

    @cached_method
    def get_device(self, device_id: str) -> QUDORABackend:
        """Get a specific IonQ device."""
        data = self.session.get_device(device_id)
        profile = self._build_profile(data)
        return QUDORABackend(profile, self.session)

    @cached_method
    def get_devices(self, **kwargs) -> list[QUDORABackend]:
        """Get a list of QUDORA devices."""
        devices = self.session.get_devices(**kwargs)
        return [QUDORABackend(self._build_profile(device), self.session) for device in devices]

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(self, "_hash", hash((self.session.token, self.session.base_url)))
        return self._hash  # pylint: disable=no-member

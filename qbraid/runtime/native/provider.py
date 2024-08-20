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
Module defining QbraidProvider class.

"""
from typing import Any, Optional

from qbraid_core.exceptions import AuthError
from qbraid_core.services.quantum import QuantumClient, QuantumServiceRequestError, process_job_data

from qbraid.programs import QPROGRAM_REGISTRY, ProgramSpec
from qbraid.runtime._display import display_jobs_from_data
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import QbraidDevice


class QbraidProvider(QuantumProvider):
    """
    This class is responsible for managing the interactions and
    authentications with qBraid Quantum services.

    Attributes:
        client (qbraid_core.services.quantum.QuantumClient): qBraid QuantumClient object
    """

    def __init__(self, api_key: Optional[str] = None, client: Optional[QuantumClient] = None):
        """
        Initializes the QbraidProvider object

        """
        if api_key and client:
            raise ValueError("Provide either api_key or client, not both.")

        self._api_key = api_key
        self._client = client

    def save_config(self, **kwargs):
        """Save the current configuration."""
        self.client.session.save_config(**kwargs)

    @property
    def client(self) -> QuantumClient:
        """Return the QuantumClient object."""
        if self._client is None:
            try:
                self._client = QuantumClient(api_key=self._api_key)
            except AuthError as err:
                raise ResourceNotFoundError(
                    "Failed to authenticate with the Quantum service."
                ) from err
        return self._client

    @staticmethod
    def _get_program_spec(run_package: Optional[str]) -> Optional[ProgramSpec]:
        if not run_package:
            return None

        program_type = QPROGRAM_REGISTRY.get(run_package)
        return ProgramSpec(program_type, alias=run_package) if program_type else None

    def _build_runtime_profile(self, device_data: dict[str, Any]) -> TargetProfile:
        """Builds a runtime profile from qBraid device data."""
        num_qubits = device_data.get("numberQubits")
        simulator = device_data.get("type") == "SIMULATOR"
        program_type_alias = device_data.get("runPackage")
        program_spec = self._get_program_spec(program_type_alias)
        return TargetProfile(
            simulator=simulator,
            device_id=device_data["qbraid_id"],
            num_qubits=num_qubits,
            program_spec=program_spec,
            provider_name="qBraid",
        )

    def get_devices(self, **kwargs) -> list[QbraidDevice]:
        """Return a list of devices matching the specified filtering."""
        query = kwargs or {}
        query["provider"] = "qBraid"

        try:
            device_data_lst = self.client.search_devices(query)
        except (ValueError, QuantumServiceRequestError) as err:
            raise ResourceNotFoundError("No devices found matching given criteria.") from err

        profiles = [self._build_runtime_profile(device_data) for device_data in device_data_lst]
        return [QbraidDevice(profile, client=self.client) for profile in profiles]

    def get_device(self, device_id: str) -> QbraidDevice:
        """Return quantum device corresponding to the specified qBraid device ID.

        Returns:
            QuantumDevice: the quantum device corresponding to the given ID

        Raises:
            ResourceNotFoundError: if device cannot be loaded from quantum service data
        """
        try:
            device_data = self.client.get_device(qbraid_id=device_id)
        except (ValueError, QuantumServiceRequestError) as err:
            raise ResourceNotFoundError(f"Device '{device_id}' not found.") from err

        profile = self._build_runtime_profile(device_data)
        return QbraidDevice(profile, client=self.client)

    # pylint: disable-next=too-many-arguments
    def display_jobs(
        self,
        device_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[dict] = None,
        max_results: int = 10,
    ):
        """Displays a list of quantum jobs submitted by user, tabulated by job ID,
        the date/time it was submitted, and status. You can specify filters to
        narrow the search by supplying a dictionary containing the desired criteria.

        Args:
            device_id (optional, str): The qBraid ID of the device used in the job.
            provider (optional, str): The name of the provider.
            tags (optional, dict): A list of tags associated with the job.
            status (optional, str): The status of the job.
            max_results (optional, int): Maximum number of results to display. Defaults to 10.
        """
        query: dict[str, Any] = {}

        if provider:
            query["provider"] = provider.lower()

        if device_id:
            query["qbraidDeviceId"] = device_id

        if status:
            query["status"] = status

        if tags:
            query.update({f"tags.{key}": value for key, value in tags.items()})

        if max_results:
            query["resultsPerPage"] = max_results

        jobs = self.client.search_jobs(query)

        job_data, msg = process_job_data(jobs, query)
        return display_jobs_from_data(job_data, msg)

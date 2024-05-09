# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for configuring provider credentials and authentication.

"""
from abc import ABC, abstractmethod
from typing import Any, Optional

from qbraid_core.exceptions import AuthError
from qbraid_core.services.quantum import QuantumClient, QuantumServiceRequestError

from qbraid.programs import QPROGRAM_REGISTRY, ProgramSpec

from .device import QbraidDevice
from .enums import DeviceType
from .exceptions import ResourceNotFoundError
from .profile import RuntimeProfile


class QuantumProvider(ABC):
    """
    This class is responsible for managing the interactions and
    authentications with various Quantum services.

    """

    def save_config(self, **kwargs):
        """Saves account data and/or credentials to the disk."""
        raise NotImplementedError

    @abstractmethod
    def get_devices(self, **kwargs):
        """Return a list of backends matching the specified filtering."""

    @abstractmethod
    def get_device(self, device_id: str):
        """Return quantum device corresponding to the specified device ID."""

    def __eq__(self, other):
        """Equality comparison.

        By default, it is assumed that two `QuantumProviders` from the same class are
        equal. Subclassed providers can override this behavior.
        """
        return type(self).__name__ == type(other).__name__


class QbraidProvider(QuantumProvider):
    """
    This class is responsible for managing the interactions and
    authentications with qBraid Quantum services.

    Attributes:
        client (qbraid_core.services.quantum.QuantumClient): qBraid QuantumClient object
    """

    def __init__(self, client: Optional[QuantumClient] = None):
        """
        Initializes the QbraidProvider object

        """
        self._client = client

    def save_config(self, **kwargs):
        """Save the current configuration."""
        self.client.session.save_config(**kwargs)

    @property
    def client(self) -> QuantumClient:
        """Return the QuantumClient object."""
        if self._client is None:
            try:
                self._client = QuantumClient()
            except AuthError as err:
                raise ResourceNotFoundError(
                    "Failed to authenticate with the Quantum service."
                ) from err
        return self._client

    def _build_runtime_profile(self, device_data: dict[str, Any]) -> RuntimeProfile:
        """Builds a runtime profile from qBraid device data."""
        num_qubits = device_data.get("numberQubits", None)
        device_type = DeviceType(device_data.get("type", "").upper())
        program_type_alias = device_data.get("runPackage", None)
        program_type = (
            QPROGRAM_REGISTRY.get(program_type_alias, None) if program_type_alias else None
        )
        program_spec = ProgramSpec(program_type, alias=program_type_alias) if program_type else None
        return RuntimeProfile(
            device_type=device_type,
            device_id=device_data["qbraid_id"],
            num_qubits=num_qubits,
            program_spec=program_spec,
        )

    def get_devices(self, **kwargs) -> list[QbraidDevice]:
        """Return a list of devices matching the specified filtering."""
        query = kwargs or {}
        query["provider"] = "qbraid"

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
            device_data = self.client.get_device(qbraid_id=device_id, provider="qbraid")
        except (ValueError, QuantumServiceRequestError) as err:
            raise ResourceNotFoundError(f"Device '{device_id}' not found.") from err

        profile = self._build_runtime_profile(device_data)
        return QbraidDevice(profile, client=self.client)

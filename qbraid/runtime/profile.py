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
Module defining the Configuration class for quantum devices, providing necessary
parameters for integration with the qBraid runtime.

"""
from collections.abc import Mapping
from typing import Any, Iterator, Optional, Union

from qbraid.programs import ProgramSpec

from .enums import DeviceActionType, DeviceType


class TargetProfile(Mapping):
    """
    Encapsulates configuration settings for a quantum device, presenting them as a read-only
    dictionary. This class primarily stores and manages settings that are crucial for the proper
    functioning and integration of quantum devices within a specified environment.

    Attributes:
        _data (dict): Internal storage for the configuration properties.
    """

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        device_id: str,
        device_type: Union[DeviceType, str],
        action_type: Optional[Union[DeviceActionType, str]] = None,
        num_qubits: Optional[int] = None,
        program_spec: Optional[ProgramSpec] = None,
        provider_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Initializes a new instance of the TargetProfile, setting up configuration according to the
        provided parameters.

        Args:
            device_id (str): Unique identifier for the device.
            device_type (DeviceType): Type of the quantum device, instance of DeviceType.
            action_type (optional, DeviceActionType): Classification of quantum program type
                compatible with the device, instance of DeviceActionType.
            num_qubits (int): Number of qubits supported by the device.
            program_spec (optional, ProgramSpec): Specification for the program, encapsulating
                program type and other metadata.
            provider_name (optional, str): Name of the quantum device provider.

        Raises:
            TypeError: If any of the inputs are not of the expected type.
            ValueError: If the device type or action type is invalid.
        """
        if not isinstance(device_id, str):
            raise TypeError("device_id must be a string")
        if isinstance(device_type, str):
            try:
                device_type = getattr(DeviceType, device_type.upper())
            except AttributeError as err:
                raise ValueError("Invalid device type") from err
        if not isinstance(device_type, DeviceType):
            raise TypeError("device_type must be an instance of DeviceType")
        if action_type:
            if isinstance(action_type, str):
                try:
                    action_type = getattr(DeviceActionType, action_type.upper())
                except AttributeError as err:
                    raise ValueError("Invalid action type") from err
            if not isinstance(action_type, DeviceActionType):
                raise TypeError("action_type must be an instance of DeviceActionType")
        if num_qubits and not isinstance(num_qubits, int):
            raise TypeError("device_num_qubits must be an integer")
        if program_spec and not isinstance(program_spec, ProgramSpec):
            raise TypeError("program_spec must be an instance of ProgramSpec")
        if provider_name and not isinstance(provider_name, str):
            raise TypeError("provider_name must be a string")

        self._data = {
            "device_id": device_id,
            "device_type": device_type.name,
            "action_type": action_type.name if action_type else None,
            "num_qubits": num_qubits,
            "program_spec": program_spec,
            "provider_name": provider_name,
            **kwargs,
        }

    def __getitem__(self, key: str) -> Any:
        """Return the value associated with the key."""
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over the keys of the configuration."""
        return iter(self._data)

    def __len__(self) -> int:
        """Return the number of items in the configuration."""
        return len(self._data)

    def __str__(self) -> str:
        """Return a string representation of the configuration."""
        return str(self._data)

    def __repr__(self) -> str:
        """Return a string representation of the configuration."""
        return f"<TargetProfile({self._data})>"

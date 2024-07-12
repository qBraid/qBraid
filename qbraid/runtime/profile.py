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
# pylint: disable=no-self-argument
from typing import Any, Iterator, Optional, Set

from pydantic import BaseModel, field_validator

from qbraid.programs import ProgramSpec

from .enums import DeviceActionType, DeviceType


class TargetProfile(BaseModel):
    """
    Encapsulates configuration settings for a quantum device, presenting them as a read-only
    dictionary. This class primarily stores and manages settings that are crucial for the proper
    functioning and integration of quantum devices within a specified environment.
    """

    device_id: str
    device_type: DeviceType
    action_type: Optional[DeviceActionType] = None
    num_qubits: Optional[int] = None
    program_spec: Optional[ProgramSpec] = None
    provider_name: Optional[str] = None
    basis_gates: Optional[Set[str]] = None

    @field_validator("device_id", "provider_name")
    def validate_device_id(cls, value: str) -> str:
        """Validate the device ID and provider name."""
        return value

    @field_validator("device_type")
    def validate_device_type(cls, value: DeviceType) -> str:
        """Validate the device type."""
        return value

    @field_validator("action_type")
    def validate_action_type(cls, value: Optional[DeviceActionType]) -> Optional[DeviceActionType]:
        """Validate the action type."""
        if value is None:
            return None

        return value

    @field_validator("basis_gates", mode="before")
    def validate_basis_gates(cls, value):
        """Validate the basis gates."""
        if value is None:
            return None
        if not isinstance(value, list) or not all(isinstance(gate, str) for gate in value):
            raise TypeError("basis_gates must be a list of strings")
        return [gate.lower() for gate in value]

    @field_validator("num_qubits")
    def validate_num_qubits(cls, value):
        """Validate the number of qubits."""
        return value

    @field_validator("program_spec")
    def validate_program_spec(cls, value):
        """Validate the program spec."""
        return value

    @field_validator("basis_gates", mode="after")
    def validate_basis_gates_after(cls, value, info):
        """Validate the basis gates after the action type is set."""
        action_type = info.data["action_type"]

        if action_type is None or action_type != "OpenQASM":
            if value is not None:
                raise ValueError("basis_gates can only be specified for OPENQASM action type")

        return value

    def items(self) -> Iterator[tuple[str, Any]]:
        """Return an iterator of key-value pairs of the profile."""
        return [(k, v) for k, v in self.__dict__.items() if v is not None]

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value of the key if it exists."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __iter__(self) -> Iterator[str]:
        for key, value in self.__dict__.items():
            if value is not None:
                yield key, value

    def __len__(self) -> int:
        return sum(1 for v in self.__dict__.values() if v is not None)

    def __str__(self) -> str:
        return f"TargetProfile({', '.join(f'{k}={v}' for k, v in self.__dict__.items())})"

    def __repr__(self) -> str:
        return f"TargetProfile {', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())}>"

    class Config:
        """Pydantic configuration settings for the TargetProfile class."""

        arbitrary_types_allowed = True
        use_enum_values = True
        extra = "allow"

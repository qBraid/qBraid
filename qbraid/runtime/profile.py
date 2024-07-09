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
from typing import Any, Iterator, List, Optional, Set, Union

from pydantic import BaseModel, field_validator, model_validator

from qbraid.programs import ProgramSpec

from .enums import DeviceActionType, DeviceType


class TargetProfile(BaseModel):
    device_id: str
    device_type: DeviceType
    action_type: Optional[DeviceActionType] = None
    num_qubits: Optional[int] = None
    program_spec: Optional[ProgramSpec] = None
    provider_name: Optional[str] = None
    basis_gates: Optional[Set[str]] = None

    @field_validator("device_id", "provider_name")
    def validate_device_id(cls, value: str) -> str:
        return value

    @field_validator("device_type")
    def validate_device_type(cls, value: DeviceType) -> str:
        return value

    @field_validator("action_type")
    def validate_action_type(cls, value: Optional[DeviceActionType]) -> Optional[str]:
        if value is None:
            return None

        return value

    @field_validator("basis_gates", mode="before")
    def validate_basis_gates(cls, value):
        if value is None:
            return None
        if not isinstance(value, list) or not all(isinstance(gate, str) for gate in value):
            raise TypeError("basis_gates must be a list of strings")
        return [gate.lower() for gate in value]

    @field_validator("num_qubits")
    def validate_num_qubits(cls, value):
        return value

    @field_validator("program_spec")
    def validate_program_spec(cls, value):
        return value

    @field_validator("basis_gates", mode="after")
    def validate_basis_gates_after(cls, value, info):
        try:
            action_type = info.data["action_type"]
        except KeyError:
            action_type = None

        if action_type is None or action_type != "OpenQASM":
            if value is not None:

                raise ValueError("basis_gates can only be specified for OPENQASM action type")
        return value

    def items(self) -> Iterator[tuple[str, Any]]:
        """Return an iterator of key-value pairs of the profile."""
        return self.__dict__.items()

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value of the key if it exists."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dict__)

    def __len__(self) -> int:
        dict_without_nones = {k: v for k, v in self.__dict__.items() if v is not None}
        return len(dict_without_nones)

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return f"<TargetProfile({self.__dict__})>"

    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True
        extra = "allow"

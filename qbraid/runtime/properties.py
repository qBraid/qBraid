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
Module defining the DeviceProperties model providing necessary
quantum device information for integration with qBraid runtime.

"""
from typing import Optional

from pydantic import BaseModel, Field

from .enums import DeviceType


class DeviceProperties(BaseModel):
    """
    Encapsulates configuration settings for a quantum device, presenting them in a structured
    and validated format using Pydantic.
    """

    device_id: str
    device_type: DeviceType
    num_qubits: Optional[int] = Field(None, description="Number of qubits supported by the device")
    max_experiments: Optional[int] = Field(
        None, description="Maximum number of experiments that can be submitted in a single batch"
    )
    min_shots: Optional[int] = Field(
        None, description="Minimum number of shots required per experiment"
    )
    max_shots: Optional[int] = Field(
        None, description="Maximum number of shots allowed per experiment"
    )
    native_get_set: Optional[list[str]] = Field(
        None, description="List of supported quantum operations"
    )

    class Config:
        """Pydantic configuration settings for DeviceProperties model."""

        use_enum_values = True
        anystr_strip_whitespace = True
        validate_assignment = True

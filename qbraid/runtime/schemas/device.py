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
Module defining qBraid runtime job schemas.

"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from .base import USD, Credits


class DevicePricing(BaseModel):
    """Represents pricing information for a quantum device.

    Attributes:
        perTask (USD): The cost per task in USD.
        perShot (USD): The cost per shot in USD.
        perMinute (USD): The cost per minute in USD.
    """

    model_config = ConfigDict(frozen=True)

    perTask: USD
    perShot: USD
    perMinute: USD

    @field_serializer("perTask", "perShot", "perMinute")
    def serialize_credits(self, value: USD) -> Credits:
        """Serialize USD fields into Credits objects."""
        return Credits(value.to_credits())


class DeviceData(BaseModel):
    """Represents metadata and capabilities of a quantum device.

    Attributes:
        provider (str): The entity that manufactures the quantum hardware or maintains the
            simulator software.
        vendor (str): The entity that hosts or provides access to the quantum device for end users.
        name (str): The name of the quantum device.
        paradigm (str): The quantum computing paradigm (e.g., gate-model, AHS).
        status (str): The current status of the device (e.g., ONLINE, OFFLINE).
        is_available (bool): Indicates whether the device is available for jobs.
        queue_depth (int, optional): The depth of the job queue, or None if not applicable.
        device_type (str): The type of device (e.g., Simulator, QPU).
        num_qubits (int): The number of qubits supported by the device.
        run_package (str): The software package used to interact with the device (e.g. qasm2).
        device_id (str): The qBraid-specific device identifier.
        noise_models (list[str], optional): A list of supported noise models. Defaults to None.
        pricing (DevicePricing): The pricing structure for using the device, in qBraid credits.
    """

    model_config = ConfigDict(frozen=True)

    provider: str
    vendor: str
    name: str
    paradigm: str
    status: str

    is_available: bool = Field(alias="isAvailable")
    queue_depth: Optional[int] = Field(None, alias="queueDepth")

    device_type: str = Field(alias="type")
    num_qubits: Optional[int] = Field(alias="numberQubits")
    run_package: str = Field(alias="runPackage")
    device_id: str = Field(alias="qbraid_id")

    noise_models: Optional[list[str]] = Field(None, alias="noiseModels")
    pricing: DevicePricing

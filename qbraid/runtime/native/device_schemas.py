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
Module defining qBraid native quantum device schemas.

"""
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class DevicePricing(BaseModel):
    """Represents pricing information for a quantum device.

    Attributes:
        perTask (Decimal): The cost per task in qBraid credits.
        perShot (Decimal): The cost per shot in qBraid credits.
        perMinute (Decimal): The cost per minute in qBraid credits.
    """

    perTask: Decimal
    perShot: Decimal
    perMinute: Decimal

    class Config:
        """Configuration settings for the DevicePricing model."""

        frozen = True


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
        queue_depth (Optional[int]): The depth of the job queue, or None if not applicable.
        device_type (str): The type of device (e.g., Simulator, QPU).
        num_qubits (int): The number of qubits supported by the device.
        run_package (str): The software package used to interact with the device (e.g. qasm2).
        device_id (str): The qBraid-specific device identifier.
        noise_models (list[str]): A list of supported noise models. Defaults to an empty list.
        pricing (DevicePricing): The pricing structure for using the device, in qBraid credits.
    """

    provider: str
    vendor: str
    name: str
    paradigm: str
    status: str

    is_available: bool = Field(alias="isAvailable")
    queue_depth: Optional[int] = Field(None, alias="queueDepth")

    device_type: str = Field(alias="type")
    num_qubits: int = Field(alias="numberQubits")
    run_package: str = Field(alias="runPackage")
    device_id: str = Field(alias="qbraid_id")

    noise_models: List[str] = Field(default_factory=list, alias="noiseModels")
    pricing: DevicePricing

    class Config:
        """Configuration settings for the DeviceData model."""

        frozen = True

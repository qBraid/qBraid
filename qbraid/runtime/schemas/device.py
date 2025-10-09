# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
        run_input_types (list[str]): The software packages / program type alises that can be
            used to specify quantum programs in jobs submitted to the device (e.g. ['qasm2']).
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
    run_input_types: list[str] = Field(alias="runInputTypes")
    device_id: str = Field(alias="qbraid_id")

    noise_models: Optional[list[str]] = Field(None, alias="noiseModels")
    pricing: Optional[DevicePricing] = None

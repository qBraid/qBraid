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
Module defining qBraid runtime schemas.

.. currentmodule:: qbraid.runtime.schemas

Models
--------

.. autosummary::
   :toctree: ../stubs/

    QbraidSchemaBase
    QbraidSchemaHeader
    DevicePricing
    DeviceData
    ExperimentMetadata
    AhsExperimentMetadata
    AnnealingExperimentMetadata
    GateModelExperimentMetadata
    QuEraQasmSimulationMetadata
    QbraidQirSimulationMetadata
    TimeStamps
    RuntimeJobModel
    QuboSolveParams

Classes
---------

.. autosummary::
   :toctree: ../stubs/

    Credits
    USD

"""
from .base import USD, Credits, QbraidSchemaBase, QbraidSchemaHeader
from .device import DeviceData, DevicePricing
from .experiment import (
    AhsExperimentMetadata,
    AnnealingExperimentMetadata,
    ExperimentMetadata,
    GateModelExperimentMetadata,
    QbraidQirSimulationMetadata,
    QuboSolveParams,
    QuEraQasmSimulationMetadata,
)
from .job import RuntimeJobModel, TimeStamps

__all__ = [
    "QbraidSchemaBase",
    "QbraidSchemaHeader",
    "DevicePricing",
    "DeviceData",
    "AhsExperimentMetadata",
    "AnnealingExperimentMetadata",
    "ExperimentMetadata",
    "GateModelExperimentMetadata",
    "QbraidQirSimulationMetadata",
    "QuboSolveParams",
    "QuEraQasmSimulationMetadata",
    "RuntimeJobModel",
    "TimeStamps",
    "Credits",
    "USD",
]

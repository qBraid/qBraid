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
Module defining the Configuration class for quantum devices, providing necessary
parameters for integration with the qBraid runtime.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qbraid.programs import ExperimentType, ProgramSpec

from .noise import NoiseModelSet

if TYPE_CHECKING:
    from typing_extensions import Self


class TargetProfile(BaseModel):
    """
    Encapsulates read-only configuration settings for a quantum device, along with
    additional data necessary to formulate the runtime protocol(s) used to submit
    quantum jobs to the device within a specified environment for a given provider.

    """

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True, frozen=True)

    device_id: str
    simulator: bool
    experiment_type: Optional[ExperimentType] = None
    num_qubits: Optional[int] = None
    program_spec: Optional[Union[ProgramSpec, list[ProgramSpec]]] = None
    provider_name: Optional[str] = None
    basis_gates: Optional[Union[list[str], set[str], tuple[str, ...]]] = None
    noise_models: Optional[NoiseModelSet] = None

    @field_validator("basis_gates")
    @classmethod
    def validate_basis_gates(cls, value) -> Optional[set[str]]:
        """Validate the basis gates."""
        if value is None:
            return None

        return {gate.lower() for gate in value}

    @model_validator(mode="after")
    def validate_basis_gates_for_experiment_type(self) -> Self:
        """Validate the basis gates for the action type."""
        if self.basis_gates is not None and self.experiment_type != ExperimentType.GATE_MODEL:
            raise ValueError("basis_gates can only be specified for gate model experiments")
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value of the key if it exists."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __len__(self) -> int:
        return sum(1 for v in self.__dict__.values() if v is not None)

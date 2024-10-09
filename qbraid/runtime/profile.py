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
    program_spec: Optional[ProgramSpec] = None
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
            raise ValueError("basis_gates can only be specified for OPENQASM action type")
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value of the key if it exists."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __len__(self) -> int:
        return sum(1 for v in self.__dict__.values() if v is not None)

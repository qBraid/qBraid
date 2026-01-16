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
Module defining qBraid runtime experiment schemas.

"""
from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qbraid.programs import load_program
from qbraid.programs.typer import Qasm2String, Qasm3String

if TYPE_CHECKING:
    from typing_extensions import Self


class ExperimentMetadata(BaseModel):
    """Base class for experiment metadata.

    This class serves as a base for more specific experiment metadata classes.
    """

    model_config = ConfigDict(extra="allow")


class GateModelExperimentMetadata(BaseModel):
    """Metadata specific to gate-model experiments, i.e. experiments defined
    using an intermediate representation (IR) that is compatible with OpenQASM.

    Attributes:
        measurement_counts (Counter): Counter for measurement outcomes.
        measurements (list, optional): Optional list of measurement results.
        qasm (str, optional): OpenQASM string representation of the quantum circuit.
        num_qubits (int, optional): Number of qubits used in the circuit.
        gate_depth (int, optional): Depth of the quantum circuit (i.e. length of critical path)
    """

    measurement_counts: Optional[Counter] = Field(None, alias="measurementCounts")
    measurements: Optional[list] = None
    qasm: Optional[str] = Field(None, alias="openQasm")
    num_qubits: Optional[int] = Field(None, alias="circuitNumQubits")
    gate_depth: Optional[int] = Field(None, alias="circuitDepth")

    @field_validator("measurement_counts")
    @classmethod
    def validate_counts(cls, value):
        """Validates and ensures that the measurement counts are a Counter object.

        Args:
            value: The measurement counts.

        Returns:
            Counter: A validated counter object.
        """
        return Counter(value)

    @field_validator("qasm")
    @classmethod
    def validate_qasm(cls, value):
        """Validates that the provided QASM is valid.

        Args:
            value: The QASM string.

        Returns:
            The validated QASM string.

        Raises:
            ValueError: If the QASM string is not valid.
        """
        if value is None:
            return value
        if not isinstance(value, (Qasm2String, Qasm3String)):
            raise ValueError("openQasm must be a valid OpenQASM string.")
        return value

    @model_validator(mode="after")
    def set_qubits_and_depth(self) -> Self:
        """Sets the number of qubits and gate depth if not already provided.

        Returns:
            Self: The updated instance with qubits and depth set.
        """
        if self.qasm and (self.num_qubits is None or self.gate_depth is None):
            program = load_program(self.qasm)
            self.num_qubits = self.num_qubits or program.num_qubits
            self.gate_depth = self.gate_depth or program.depth  # type: ignore

        return self


class AhsExperimentMetadata(BaseModel):
    """Metadata specific to Analog Hamiltonian Simulation (AHS) experiments.

    Attributes:
        measurement_counts (Counter): Counter for measurement outcomes
        measurements (list, optional): Optional list of measurement results
        num_atoms (int, optional): Number of atoms (sites) used to build lattice structure
        sites (list[tuple[float, float]], optional): Vector positions of atoms in meters
        filling (list[int], optional): List of ints {0,1} indicating the filling status at each site
    """

    measurement_counts: Optional[Counter] = Field(None, alias="measurementCounts")
    measurements: Optional[list[dict[str, Union[bool, Optional[list[int]]]]]] = None
    num_atoms: Optional[int] = Field(None, alias="numAtoms")
    sites: Optional[list[tuple[float, float]]] = None
    filling: Optional[list[int]] = None

    @field_validator("filling")
    @classmethod
    def validate_filling(cls, value):
        """Validates and ensures that the fillings are integers 0 or 1.

        Args:
            value: The filling status at each site.

        Returns:
            list[int]: A validated list of integers.
        """
        if value is None:
            return value

        def validate_item(item):
            int_item = int(item)
            if int_item not in {0, 1}:
                raise ValueError(f"Invalid filling value: {item}. Must be 0 or 1.")
            return int_item

        try:
            return [validate_item(filling) for filling in value]
        except ValueError as err:
            raise ValueError(
                "Invalid filling value. Must be a list of integers, each either 0 or 1."
            ) from err

    @model_validator(mode="after")
    def validate_ahs(self) -> Self:
        """Validates that the sites, filling, and num_atoms lengths match.

        Returns:
            Self: The updated instance with validated lengths.
        """
        lengths = {
            "sites": len(self.sites) if self.sites else None,
            "filling": len(self.filling) if self.filling else None,
            "num_atoms": self.num_atoms,
        }

        filtered_lengths = {k: v for k, v in lengths.items() if v is not None}

        if len(set(filtered_lengths.values())) > 1:
            mismatched = ", ".join(f"{k}: {v}" for k, v in filtered_lengths.items())
            raise ValueError(
                "The lengths of 'sites', 'filling', and value of 'num_atoms' must be consistent. "
                f"Detected mismatched values: {mismatched}"
            )

        if self.num_atoms is None and filtered_lengths:
            self.num_atoms = next(iter(filtered_lengths.values()))

        return self


class AnnealingExperimentMetadata(BaseModel):
    """Metadata specific to annealing experiments."""

    solutions: Optional[list[dict[str, Any]]] = None
    num_solutions: Optional[int] = Field(None, alias="solutionCount")
    energies: Optional[list[float]] = None
    num_variables: Optional[int] = Field(None, alias="numVariables")

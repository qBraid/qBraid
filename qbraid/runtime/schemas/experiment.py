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
Module defining qBraid runtime experiment schemas.

"""
from __future__ import annotations

from collections import Counter
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Self

from qbraid.programs import load_program
from qbraid.programs.typer import Qasm2String, Qasm3String


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


class QbraidQirSimulationMetadata(GateModelExperimentMetadata):
    """Result data specific to jobs submitted to the qBraid QIR simulator.

    Attributes:
        backend_version (str, optional): The version of the simulator backend.
        seed (int, optional): The seed used for the simulation.

    """

    backend_version: Optional[str] = Field(None, alias="runnerVersion")
    seed: Optional[int] = Field(None, alias="runnerSeed")


class QuEraQasmSimulationMetadata(GateModelExperimentMetadata):
    """Result data specific to jobs submitted to the QuEra QASM simulator.

    Attributes:
        backend (str, optional): The name of the backend used for the simulation.
        flair_visual_version (str, optional): The version of the Flair Visual
            tool used to generate the atom animation state data.
        atom_animation_state (dict, optional): JSON data representing the state
            of the QPU atoms used in the simulation.
        logs (list, optional): List of log messages generated during the simulation.

    """

    backend: Optional[str] = None
    flair_visual_version: Optional[str] = Field(None, alias="flairVisualVersion")
    atom_animation_state: Optional[dict[str, Any]] = Field(None, alias="atomAnimationState")
    logs: Optional[list[dict[str, Any]]] = None

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
        logs (list, optional): list of log messages generated during the simulation.

    """

    backend: Optional[str] = None
    flair_visual_version: Optional[str] = Field(None, alias="flairVisualVersion")
    atom_animation_state: Optional[dict[str, Any]] = Field(None, alias="atomAnimationState")
    logs: Optional[list[dict[str, Any]]] = None


class AnnealingExperimentMetadata(BaseModel):
    """Metadata specific to annealing experiments."""

    solutions: Optional[list[dict[str, Any]]] = None
    num_solutions: Optional[int] = Field(None, alias="solutionCount")
    energies: Optional[list[float]] = None
    num_variables: Optional[int] = Field(None, alias="variableCount")


class QuboSolveParams(BaseModel):
    """Parameters for solving a QUBO problem using NEC VA algorithm.

    Attributes:
        offset (float): Offset for the normalized weight information stored in the QUBO.
        num_reads (Optional[int]): VA sampling rate. Must be between 1 and 20. Default is 1.
        num_results (Optional[int]): Number of VA annealing results. Returns only the optimal
            solution when 1 or None is specified. Default is 1.
        num_sweeps (Optional[int]): Number of VA annealing sweeps. Must be between 1 and 100000.
            Default is 500.
        beta_range (Optional[tuple[float, float, int]]): VA beta value in (start, end, steps)
            format. Default is (10.0, 100.0, 200).
        beta_list (Optional[list[float]]): Beta value array for each VA sweep.
        dense (Optional[bool]): VA matrix mode. True for dense matrix mode, False for sparse
            matrix mode. Default is None.
        vector_mode (Optional[str]): Mode during VA annealing. Options are 'speed' for speed
            priority or 'accuracy' for accuracy priority. Default is 'accuracy'.
        timeout (Optional[int]): Job execution timeout in seconds. Standard range is between 1
            and 7200. Default is 1800.
        ve_num (Optional[int]): Number of VEs used in VA annealing. Must be between 1 and the
            number of VEs installed on each server.
        onehot (Optional[list[str]]): VA onehot constraint parameter.
        fixed (Optional[Union[dict[str, int], list[str]]]): VA fixed constraint parameter.
        andzero (Optional[list[str]]): VA andzero constraint parameter.
        orone (Optional[list[str]]): VA orone constraint parameter.
        supplement (Optional[list[str]]): VA supplement constraint parameter.
        maxone (Optional[list[str]]): VA maxone constraint parameter.
        minmaxone (Optional[list[str]]): VA minmaxone constraint parameter.
        init_spin (Optional[Union[dict[str, int], list[str]]]): VA init_spin parameter.
        spin_list (Optional[list[str]]): VA spin_list parameter.
    """

    offset: float

    num_reads: Optional[int] = 1
    num_results: Optional[int] = 1
    num_sweeps: Optional[int] = 500
    beta_range: Optional[tuple[float, float, int]] = (10.0, 100.0, 200)
    beta_list: Optional[list[float]] = None
    dense: Optional[bool] = None

    vector_mode: Optional[str] = "accuracy"
    timeout: Optional[int] = 1800
    ve_num: Optional[int] = None
    onehot: Optional[list[str]] = None
    fixed: Optional[Union[dict[str, int], list[str]]] = None
    andzero: Optional[list[str]] = None
    orone: Optional[list[str]] = None
    supplement: Optional[list[str]] = None
    maxone: Optional[list[str]] = None
    minmaxone: Optional[list[str]] = None
    init_spin: Optional[Union[dict[str, int], list[str]]] = None
    spin_list: Optional[list[str]] = None

    @field_validator("offset")
    @classmethod
    def validate_offset(cls, value):
        """Validate the offset value."""
        if not -3.402823e38 <= value <= 3.402823e38:
            raise ValueError("offset must be between -3.402823e+38 and 3.402823e+38")
        return value

    @field_validator("num_reads")
    @classmethod
    def validate_num_reads(cls, value):
        """Validate the num_reads value."""
        if value is not None and not 1 <= value <= 20:
            raise ValueError("num_reads must be between 1 and 20")
        return value

    @field_validator("num_sweeps")
    @classmethod
    def validate_num_sweeps(cls, value):
        """Validate the num_sweeps value."""
        if value is not None and not 1 <= value <= 100000:
            raise ValueError("num_sweeps must be between 1 and 100000")
        return value

    @field_validator("beta_range")
    @classmethod
    def validate_beta_range(cls, value):
        """Validate the beta_range value."""
        start, end, steps = value

        min_value = 1.1754945e-38
        max_value = 3.402823e38

        if not min_value <= start <= max_value:
            raise ValueError(f"start value must be between {min_value} and {max_value}")

        if not min_value <= end <= max_value:
            raise ValueError(f"end value must be between {min_value} and {max_value}")

        if start > end:
            raise ValueError("start value must be less than or equal to end value")

        if not 1 <= steps <= 100000:
            raise ValueError("steps must be between 1 and 100000")

        return value

    @field_validator("beta_list")
    @classmethod
    def validate_beta_list(cls, value):
        """Validate the beta_list value."""
        if value is None:
            return value

        min_value = 1.1754945e-38
        max_value = 3.402823e38

        for beta in value:
            if not min_value <= beta <= max_value:
                raise ValueError(
                    f"All beta values must be between {min_value} and {max_value}. "
                    f"Found invalid value: {beta}"
                )

        return value

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, value):
        """Validate the timeout value."""
        if value is not None and not 1 <= value <= 7200:
            raise ValueError("timeout must be between 1 and 7200 seconds")
        return value

    @field_validator("vector_mode")
    @classmethod
    def validate_vector_mode(cls, value):
        """Validate the vector_mode value."""
        if value is not None and value not in {"speed", "accuracy"}:
            raise ValueError("vector_mode must be 'speed' or 'accuracy'")
        return value

    @field_validator("ve_num")
    @classmethod
    def validate_ve_num(cls, value):
        """Validate the ve_num value."""
        if value is not None and value < 1:
            raise ValueError("ve_num must be greater than or equal to 1")
        return value

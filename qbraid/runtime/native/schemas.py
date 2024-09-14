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
Module defining qBraid native runtime schemas.

"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Annotated, Self

from qbraid.programs import load_program
from qbraid.programs.typer import Qasm2String, Qasm3String
from qbraid.runtime.enums import ExperimentType, JobStatus, NoiseModel


class QbraidSchemaHeader(BaseModel):
    """Represents the header for a qBraid schema.

    Attributes:
        name (str): Name of the schema.
        version (float): Version number of the schema.
    """

    name: Annotated[str, Field(strict=True, min_length=1)]
    version: Annotated[float, Field(strict=True, gt=0)]


class QbraidSchemaBase(BaseModel):
    """Base class for qBraid schemas with a predefined header.

    Attributes:
        header (QbraidSchemaHeader): The schema header.
    """

    header: QbraidSchemaHeader = Field(
        alias="schemaHeader", default=QbraidSchemaHeader(name="qbraid.runtime.native", version=1.0)
    )


class ExperimentMetadata(BaseModel):
    """Base class for experiment metadata.

    This class serves as a base for more specific experiment metadata classes.
    """

    model_config = ConfigDict(extra="allow")


class GateModelExperimentMetadata(BaseModel):
    """Metadata specific to qBraid gate-model experiments.

    Attributes:
        qasm (Optional[str]): OpenQASM string representation of the quantum circuit.
        num_qubits (Optional[int]): Number of qubits used in the circuit.
        gate_depth (Optional[int]): Depth of the quantum gate circuit.
        noise_model (Optional[NoiseModel]): Noise model used in the experiment.
        measurement_counts (Counter): Counter for measurement outcomes.
        measurements (Optional[list]): Optional list of measurement results.
    """

    qasm: Optional[str] = Field(None, alias="openQasm")
    num_qubits: Optional[int] = Field(None, alias="circuitNumQubits")
    gate_depth: Optional[int] = Field(None, alias="circuitDepth")
    noise_model: Optional[NoiseModel] = Field(None, alias="noiseModel")
    measurement_counts: Optional[Counter] = Field(None, alias="measurementCounts")
    measurements: Optional[list] = None

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


class TimeStamps(BaseModel):
    """Model for capturing time-related information in an experiment.

    Attributes:
        createdAt (datetime): Timestamp when the job was created.
        endedAt (datetime): Timestamp when the job ended.
        executionDuration (float): Duration of execution in milliseconds.
    """

    createdAt: datetime
    endedAt: datetime
    executionDuration: float = Field(gt=0, description="Execution time in milliseconds")

    @field_validator("createdAt", "endedAt", mode="before")
    @classmethod
    def parse_datetimes(cls, value):
        """Parses the timestamps into datetime objects.

        Args:
            value: The timestamp string.

        Returns:
            datetime: Parsed datetime object.
        """
        if value:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        return value


class RuntimeJobModel(QbraidSchemaBase):
    """Represents a runtime job in the qBraid platform.

    Attributes:
        job_id (str): The unique identifier for the job.
        device_id (str): The identifier of the quantum device used.
        status (JobStatus): The current status of the job.
        shots (Optional[int]): The number of shots for the quantum experiment.
        experiment_type (ExperimentType): The type of experiment conducted.
        metadata (Union[QbraidExperimentMetadata, ExperimentMetadata]): Metadata associated
            with the experiment.
        time_stamps (TimeStamps): Time-related information about the job.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    job_id: str = Field(..., alias="qbraidJobId")
    device_id: str = Field(..., alias="qbraidDeviceId")
    status: JobStatus
    shots: Optional[int] = Field(None, gt=0)
    experiment_type: ExperimentType = Field(..., alias="experimentType")
    metadata: Union[GateModelExperimentMetadata, ExperimentMetadata]
    time_stamps: TimeStamps = Field(..., alias="timeStamps")

    @staticmethod
    def _populate_metadata(
        job_data: dict[str, Any], experiment_type: ExperimentType
    ) -> dict[str, Any]:
        """Populates metadata in the job data based on the experiment type.

        Args:
            job_data (dict): The original job data.
            experiment_type (ExperimentType): The type of experiment being processed.

        Returns:
            dict[str, Any]: The updated job data with the appropriate metadata fields populated.
        """
        if experiment_type == ExperimentType.GATE_MODEL:
            keys = [
                field.alias or name
                for name, field in GateModelExperimentMetadata.model_fields.items()
            ]
            metadata = {key: job_data.pop(key, None) for key in keys}
            job_data["metadata"] = GateModelExperimentMetadata(**metadata)
            return job_data

        model_keys = {field.alias or name for name, field in RuntimeJobModel.model_fields.items()}

        restructured_job_data: dict[str, Any] = {}
        derived_metadata: dict[str, Any] = {}

        for key, value in job_data.items():
            if key in model_keys:
                restructured_job_data[key] = value
            else:
                derived_metadata[key] = value

        restructured_job_data["metadata"] = ExperimentMetadata(**derived_metadata)
        return restructured_job_data

    @classmethod
    def from_dict(cls, job_data: dict[str, Any]) -> RuntimeJobModel:
        """Creates a RuntimeJobModel instance from a dictionary of job data.

        Args:
            job_data (dict): Dictionary containing job data.

        Returns:
            RuntimeJobModel: An instance of RuntimeJobModel.
        """
        experiment_type = ExperimentType(job_data.pop("experimentType", "gate_model"))
        job_data["experimentType"] = experiment_type

        if "metadata" not in job_data:
            job_data = cls._populate_metadata(job_data, experiment_type)

        status = job_data.get("status")
        status_message = job_data.pop("statusText", None)

        if status_message:
            if isinstance(status, str):
                job_data["status"] = JobStatus(status)
            if isinstance(job_data["status"], JobStatus):
                job_data["status"].set_status_message(status_message)

        return cls(**job_data)

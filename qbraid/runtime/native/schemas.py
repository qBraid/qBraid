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

from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import Annotated

from qbraid.runtime.enums import ExperimentType, JobStatus
from qbraid.runtime.schemas import ExperimentMetadata, GateModelExperimentMetadata


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


class TimeStamps(BaseModel):
    """Model for capturing time-related information in an experiment.

    Attributes:
        createdAt (datetime): Timestamp when the job was created.
        endedAt (datetime): Timestamp when the job ended.
        executionDuration (float): Duration of execution in milliseconds.
    """

    createdAt: datetime
    endedAt: datetime
    executionDuration: int = Field(gt=0, description="Execution time in milliseconds")

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
    metadata: Union[
        QbraidQirSimulationMetadata,
        QuEraQasmSimulationMetadata,
        GateModelExperimentMetadata,
        ExperimentMetadata,
    ]
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
            native_models = {
                "qbraid_qir_simulator": QbraidQirSimulationMetadata,
                "quera_qasm_simulator": QuEraQasmSimulationMetadata,
            }
            device_id = job_data.get("qbraidDeviceId")
            model: GateModelExperimentMetadata = native_models.get(
                device_id, GateModelExperimentMetadata
            )
            keys = {field.alias or name for name, field in model.model_fields.items()}
            metadata = {key: job_data.pop(key, None) for key in keys}
            job_data["metadata"] = model(**metadata)
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
        if "qbraidJobId" not in job_data and "job_id" in job_data:
            job_data["qbraidJobId"] = job_data.pop("job_id")

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

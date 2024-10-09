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
Module defining qBraid runtime job schemas.

"""
from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from qbraid.programs import ExperimentType
from qbraid.runtime.enums import JobStatus

from .base import Credits, QbraidSchemaBase
from .experiment import (
    AnnealingExperimentMetadata,
    ExperimentMetadata,
    GateModelExperimentMetadata,
    QbraidQirSimulationMetadata,
    QuEraQasmSimulationMetadata,
)


class TimeStamps(BaseModel):
    """Model for capturing time-related information in an experiment.

    Attributes:
        createdAt (datetime): Timestamp when the job was created.
        endedAt (datetime, optional): Timestamp when the job ended.
        executionDuration (int, optional): Duration of execution in milliseconds.
    """

    createdAt: datetime
    endedAt: Optional[datetime] = None
    executionDuration: Optional[int] = Field(
        default=None, gt=0, description="Execution time in milliseconds"
    )

    @field_validator("createdAt", "endedAt", mode="before")
    @classmethod
    def parse_datetimes(cls, value):
        """Parses the timestamps into datetime objects.

        Args:
            value: The timestamp string.

        Returns:
            datetime: Parsed datetime object or None if value is not provided.
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
        experiment_type (str): The type of experiment conducted.
        metadata (Union[QbraidExperimentMetadata, ExperimentMetadata]): Metadata associated
            with the experiment.
        time_stamps (TimeStamps): Time-related information about the job.
        tags (dict[str, str]): Custom tags associated with the job.
        cost (Credits, optional): The cost of the job in qBraid credits.
    """

    model_config = ConfigDict(frozen=True, use_enum_values=False)

    VERSION: ClassVar[float] = 1.0

    job_id: str = Field(..., alias="qbraidJobId")
    device_id: str = Field(..., alias="qbraidDeviceId")
    status: JobStatus
    status_text: Optional[str] = Field(None, alias="statusText")
    shots: Optional[int] = Field(None, ge=0)
    experiment_type: ExperimentType = Field(..., alias="experimentType")
    metadata: Union[
        QbraidQirSimulationMetadata,
        QuEraQasmSimulationMetadata,
        GateModelExperimentMetadata,
        AnnealingExperimentMetadata,
        ExperimentMetadata,
    ]
    time_stamps: TimeStamps = Field(..., alias="timeStamps")
    tags: dict[str, str] = Field(default_factory=dict)
    cost: Optional[Credits] = Field(None, ge=0, alias="cost")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value):
        """Ensure the status is a valid JobStatus enum value."""
        members = {status.value for status in list(JobStatus)}
        if value not in members:
            raise ValueError(f"Invalid status: '{value}'. Must be one of {members}.")
        return value

    @field_validator("experiment_type", mode="before")
    @classmethod
    def validate_experiment_type(cls, value):
        """Ensure the experiment_type is a valid ExperimentType enum value."""
        members = {exp_type.value for exp_type in list(ExperimentType)}
        if value not in members:
            raise ValueError(f"Invalid experiment_type: '{value}'. Must be one of {members}.")
        return value

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
        native_gate_models = {
            "qbraid_qir_simulator": QbraidQirSimulationMetadata,
            "quera_qasm_simulator": QuEraQasmSimulationMetadata,
        }
        if experiment_type == "gate_model":
            device_id = job_data.get("qbraidDeviceId")
            model = native_gate_models.get(device_id, GateModelExperimentMetadata)
        elif experiment_type == "annealing":
            model = AnnealingExperimentMetadata

        if experiment_type in ["gate_model", "annealing"]:
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
        experiment_type = (
            "annealing"
            if "anneal" in job_data.get("qbraidDeviceId", "")
            else job_data.pop("experimentType", "gate_model")
        )
        job_data["experimentType"] = ExperimentType(experiment_type).value

        # Populate time stamps
        time_stamps = job_data.setdefault("timeStamps", {})
        created_at = job_data.get("createdAt")
        if created_at is not None and "createdAt" not in time_stamps:
            time_stamps["createdAt"] = created_at

        # Populate metadata
        if "metadata" not in job_data:
            job_data = cls._populate_metadata(job_data, job_data["experimentType"])

        # Set status
        status = job_data.get("status")
        if isinstance(status, str):
            status = JobStatus(status)
        if isinstance(status, JobStatus):
            job_data["status"] = status.value

        job_data.setdefault(
            "statusText", status.status_message if isinstance(status, JobStatus) else None
        )
        return cls(**job_data)

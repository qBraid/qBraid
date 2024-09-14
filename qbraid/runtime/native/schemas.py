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

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Annotated, Self

from qbraid.programs import load_program
from qbraid.programs.typer import Qasm2String, Qasm3String
from qbraid.runtime.enums import ExperimentType, JobStatus, NoiseModel


class QbraidSchemaHeader(BaseModel):

    name: Annotated[str, Field(strict=True, min_length=1)]
    version: Annotated[float, Field(strict=True, gt=0)]


class QbraidSchemaBase(BaseModel):

    header: QbraidSchemaHeader = Field(
        alias="schemaHeader", default=QbraidSchemaHeader(name="qbraid.runtime.native", version=1.0)
    )


class ExperimentMetadata(BaseModel):
    """Runtime Experiment base class."""

    model_config = ConfigDict(extra="allow")


class QbraidExperimentMetadata(BaseModel):
    qasm: Optional[str] = Field(None, alias="openQasm")
    num_qubits: Optional[int] = Field(None, alias="circuitNumQubits")
    gate_depth: Optional[int] = Field(None, alias="circuitDepth")
    noise_model: Optional[NoiseModel] = Field(None, alias="noiseModel")
    measurement_counts: Counter = Field(default_factory=Counter, alias="measurementCounts")
    measurements: Optional[list]

    @field_validator("qasm")
    @classmethod
    def validate_qasm(cls, value):
        if value is None:
            return value
        if not isinstance(value, (Qasm2String, Qasm3String)):
            raise ValueError("openQasm must be a valid OpenQASM string.")
        return value

    @model_validator(mode="after")
    def set_qubits_and_depth(self) -> Self:
        """Set num_qubits and depth if None and qasm is provided."""
        if self.qasm and (self.num_qubits is None or self.gate_depth is None):
            program = load_program(self.qasm)
            self.num_qubits = self.num_qubits or program.num_qubits
            self.gate_depth = self.gate_depth or program.depth  # type: ignore

        return self

    @field_validator("measurement_counts")
    @classmethod
    def validate_counts(cls, value):
        return Counter(value)


class TimeStamps(BaseModel):

    createdAt: datetime
    endedAt: datetime
    executionDuration: float = Field(gt=0, description="Execution time in milliseconds")

    @field_validator("createdAt", "endedAt", mode="before")
    def parse_datetimes(cls, value):
        if value:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        return value


class RuntimeJobModel(QbraidSchemaBase):

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    job_id: str = Field(..., alias="qbraidJobId")
    device_id: str = Field(..., alias="qbraidDeviceId")
    status: JobStatus
    shots: Optional[int] = Field(None, gt=0)
    experiment_type: ExperimentType = Field(..., alias="experimentType")
    metadata: Union[QbraidExperimentMetadata, ExperimentMetadata]
    time_stamps: TimeStamps = Field(..., alias="timeStamps")

    @classmethod
    def from_dict(cls, job_data: dict[str, Any]) -> RuntimeJobModel:
        provider: str = job_data.get("provider", "")

        if provider.lower() == "qbraid":
            keys = [
                field.alias or name for name, field in QbraidExperimentMetadata.model_fields.items()
            ]
            metadata = {key: job_data.pop(key, None) for key in keys}
            job_data["metadata"] = QbraidExperimentMetadata(**metadata)
            job_data["experimentType"] = ExperimentType.GATE_MODEL
        elif "metadata" not in job_data:
            model_keys = {
                field.alias or name for name, field in RuntimeJobModel.model_fields.items()
            }

            matched_fields: dict[str, Any] = {}
            non_matched_fields: dict[str, Any] = {}

            for key, value in job_data.items():
                if key in model_keys:
                    matched_fields[key] = value
                else:
                    non_matched_fields[key] = value

            job_data = matched_fields
            job_data["metadata"] = non_matched_fields

        status = job_data.get("status")
        status_message = job_data.pop("statusText", None)

        if status_message:
            if isinstance(status, str):
                job_data["status"] = JobStatus(status)
            if isinstance(job_data["status"], JobStatus):
                job_data["status"].set_status_message(status_message)

        return cls(**job_data)

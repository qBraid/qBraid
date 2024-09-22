# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests native runtime job schemas.

"""
import textwrap
from collections import Counter
from datetime import datetime

import pytest
from pydantic import ValidationError

from qbraid.runtime.enums import ExperimentType, JobStatus
from qbraid.runtime.native.schemas import (
    QbraidSchemaBase,
    QbraidSchemaHeader,
    RuntimeJobModel,
    TimeStamps,
)
from qbraid.runtime.schemas import ExperimentMetadata, GateModelExperimentMetadata


@pytest.fixture
def valid_qasm() -> str:
    """Returns a valid qasm string."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    h q[0];
    cx q[0],q[1];
    cx q[1],q[0];
    """
    return textwrap.dedent(qasm).strip()


def test_qbraid_schema_header():
    """Test QbraidSchemaHeader class."""
    header = QbraidSchemaHeader(name="TestSchema", version=1.0)
    assert header.name == "TestSchema"
    assert header.version == 1.0

    with pytest.raises(ValidationError):
        QbraidSchemaHeader(name="", version=1.0)  # Invalid name

    with pytest.raises(ValidationError):
        QbraidSchemaHeader(name="TestSchema", version=0)  # Invalid version


def test_qbraid_schema_base():
    """Test QbraidSchemaBase class."""
    base = QbraidSchemaBase()
    assert base.header.name == "qbraid.runtime.native"  # pylint: disable=no-member
    assert base.header.version == 1.0  # pylint: disable=no-member


def test_gate_model_experiment_metadata(valid_qasm):
    """Test GateModelExperimentMetadata class."""
    metadata = GateModelExperimentMetadata(
        openQasm=valid_qasm,
        measurementCounts=Counter({"00": 10, "01": 15}),
    )
    assert metadata.qasm == valid_qasm
    assert metadata.num_qubits == 2
    assert metadata.gate_depth == 3
    assert metadata.measurement_counts == Counter({"00": 10, "01": 15})

    with pytest.raises(ValidationError):
        GateModelExperimentMetadata(openQasm="invalid qasm string")


def test_validate_counts():
    """Test validate_counts method."""
    valid_counts = Counter({"00": 10, "01": 20})
    validated_counts = GateModelExperimentMetadata.validate_counts(valid_counts)
    assert validated_counts == valid_counts

    invalid_counts = {"00": 10, "01": 20}
    validated_counts = GateModelExperimentMetadata.validate_counts(invalid_counts)
    assert isinstance(validated_counts, Counter)


def test_timestamps():
    """Test TimeStamps class."""
    created_at_obj = datetime(2024, 9, 14, 1, 6, 34, 0)
    ended_at_obj = datetime(2024, 9, 14, 1, 6, 35, 0)

    created_at_str = "2024-09-14T01:06:34.000Z"
    ended_at_str = "2024-09-14T01:06:35.000Z"

    duration = 60000

    time_stamps = TimeStamps(
        createdAt=created_at_str, endedAt=ended_at_str, executionDuration=duration
    )
    assert time_stamps.createdAt == created_at_obj
    assert time_stamps.endedAt == ended_at_obj
    assert time_stamps.executionDuration == duration

    with pytest.raises(ValidationError):
        TimeStamps(
            createdAt="invalid date", endedAt=ended_at_str, executionDuration=duration
        )  # Invalid date format

    with pytest.raises(ValidationError):
        TimeStamps(
            createdAt=created_at_str, endedAt=ended_at_str, executionDuration=-1
        )  # Invalid executionDuration


@pytest.fixture
def mock_job_data(valid_qasm):
    """Return mock job data."""
    return {
        "qbraidJobId": "job_123",
        "qbraidDeviceId": "device_456",
        "status": "COMPLETED",
        "shots": 100,
        "experimentType": "gate_model",
        "openQasm": valid_qasm,
        "circuitNumQubits": 2,
        "circuitDepth": 2,
        "timeStamps": {
            "createdAt": "2024-09-14T01:06:34.000Z",
            "endedAt": "2024-09-14T01:06:35.000Z",
            "executionDuration": 60000,
        },
    }


def test_runtime_job_model(mock_job_data):
    """Test RuntimeJobModel class."""

    job = RuntimeJobModel.from_dict(mock_job_data)
    assert job.job_id == "job_123"
    assert job.device_id == "device_456"
    assert job.status == JobStatus.COMPLETED.value
    assert job.shots == 100
    assert isinstance(job.metadata, GateModelExperimentMetadata)
    assert job.time_stamps.executionDuration == 60000  # pylint: disable=no-member

    # Test job with missing metadata
    mock_job_data.pop("metadata", None)
    job = RuntimeJobModel.from_dict(mock_job_data)
    assert isinstance(job.metadata, GateModelExperimentMetadata)

    with pytest.raises(ValueError):
        RuntimeJobModel.from_dict(
            {"qbraidJobId": "job_123", "qbraidDeviceId": "device_456", "status": "invalid_status"}
        )


def test_populate_metadata(valid_qasm):
    """Test _populate_metadata method."""
    job_data = {"openQasm": valid_qasm, "circuitNumQubits": 5, "circuitDepth": 10}
    experiment_type = ExperimentType.GATE_MODEL
    populated_data = RuntimeJobModel._populate_metadata(job_data, experiment_type)
    assert isinstance(populated_data["metadata"], GateModelExperimentMetadata)
    assert populated_data["metadata"].qasm == valid_qasm

    experiment_type = ExperimentType.AHS
    populated_data = RuntimeJobModel._populate_metadata(job_data, experiment_type)
    assert isinstance(populated_data["metadata"], ExperimentMetadata)


def test_runtime_job_model_metadata_population():
    """Test metadata population in RuntimeJobModel."""
    job_data = {
        "qbraidJobId": "job_123",
        "qbraidDeviceId": "device_456",
        "status": "CANCELLED",
        "shots": 100,
        "experimentType": "analog_hamiltonian_simulation",
        "someAdditionalField": "extra data",
        "timeStamps": {
            "createdAt": "2024-09-14T01:06:34.000Z",
            "endedAt": "2024-09-14T01:06:35.000Z",
            "executionDuration": 60000,
        },
    }
    job = RuntimeJobModel.from_dict(job_data)
    assert isinstance(job.metadata, ExperimentMetadata)
    assert job.metadata.someAdditionalField == "extra data"


def test_time_stamps_created_at_fallback():
    """Test fallback to createdAt for TimeStamps."""
    job_data = {
        "qbraidJobId": "job_123",
        "qbraidDeviceId": "device_456",
        "status": "RUNNING",
        "shots": 100,
        "experimentType": "analog_hamiltonian_simulation",
        "createdAt": "2024-09-14T01:06:34.000Z",
    }
    job = RuntimeJobModel.from_dict(job_data)

    # pylint: disable=no-member
    assert job.time_stamps.createdAt == datetime(2024, 9, 14, 1, 6, 34, 0)
    assert job.time_stamps.endedAt is None
    assert job.time_stamps.executionDuration is None
    # pylint: enable=no-member


def test_invalid_experiment_type_raises_error(mock_job_data):
    """Test invalid experiment type raises error."""
    bad_type = "unsupported type"
    mock_job_data["experimentType"] = bad_type
    with pytest.raises(ValueError) as exc_info:
        RuntimeJobModel.from_dict(mock_job_data)
    assert str(exc_info.value).startswith(f"'{bad_type}' is not a valid ExperimentType")


def test_invalid_status_raises_error(mock_job_data):
    """Test invalid job status raises error."""
    bad_type = "unsupported type"
    mock_job_data["status"] = bad_type
    with pytest.raises(ValueError) as exc_info:
        RuntimeJobModel.from_dict(mock_job_data)
    assert str(exc_info.value).startswith(f"'{bad_type}' is not a valid JobStatus")

    with pytest.raises(ValidationError) as exc_info:
        RuntimeJobModel(**mock_job_data)
    assert f"Invalid status: '{bad_type}'" in str(exc_info.value)


def test_parse_datetimes_for_none_type(mock_job_data):
    """Test that TimeStamps model can handle None values."""
    time_stamps = mock_job_data["timeStamps"]
    time_stamps["endedAt"] = None
    time_stamps_model = TimeStamps(**time_stamps)
    assert time_stamps_model.endedAt is None

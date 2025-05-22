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
from collections import Counter
from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import BaseModel, ValidationError

from qbraid.programs import ExperimentType
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.schemas.base import USD, Credits, QbraidSchemaBase, QbraidSchemaHeader
from qbraid.runtime.schemas.device import DeviceData, DevicePricing
from qbraid.runtime.schemas.experiment import (
    AhsExperimentMetadata,
    ExperimentMetadata,
    GateModelExperimentMetadata,
    QuboSolveParams,
)
from qbraid.runtime.schemas.job import RuntimeJobModel, TimeStamps


@pytest.fixture
def mock_job_data(valid_qasm2_no_meas):
    """Return mock job data."""
    return {
        "qbraidJobId": "job_123",
        "qbraidDeviceId": "device_456",
        "status": "COMPLETED",
        "shots": 100,
        "experimentType": "gate_model",
        "openQasm": valid_qasm2_no_meas,
        "circuitNumQubits": 2,
        "circuitDepth": 2,
        "timeStamps": {
            "createdAt": "2024-09-14T01:06:34.000Z",
            "endedAt": "2024-09-14T01:06:35.000Z",
            "executionDuration": 60000,
        },
    }


def test_qbraid_schema_header():
    """Test QbraidSchemaHeader class."""
    header = QbraidSchemaHeader(name="TestSchema", version=1.0)
    assert header.name == "TestSchema"
    assert header.version == 1.0

    with pytest.raises(ValidationError):
        QbraidSchemaHeader(name="", version=1.0)  # Invalid name

    with pytest.raises(ValidationError):
        QbraidSchemaHeader(name="TestSchema", version=0)  # Invalid version


def test_qbraid_schema_base_raises_for_no_version():
    """Test QbraidSchemaBase raises ValueError when accessing header property."""
    with pytest.raises(ValueError) as excinfo:
        _ = QbraidSchemaBase()
    assert "QbraidSchemaBase must define a valid semantic version for 'VERSION'." in str(
        excinfo.value
    )


def test_qbraid_schema_base():
    """Test QbraidSchemaBase class."""

    class TestSchema(QbraidSchemaBase):
        """Test schema class."""

        VERSION = 6.1

    model = TestSchema()
    assert model.header.name == "tests.runtime.test_schemas"
    assert model.header.version == 6.1


def test_gate_model_experiment_metadata(valid_qasm2_no_meas):
    """Test GateModelExperimentMetadata class."""
    metadata = GateModelExperimentMetadata(
        openQasm=valid_qasm2_no_meas,
        measurementCounts=Counter({"00": 10, "01": 15}),
    )
    assert metadata.qasm == valid_qasm2_no_meas
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


def test_execution_duration_auto_calculation():
    """Test execution duration auto-calculation."""
    created = datetime(2025, 5, 22, 15, 8, 57)
    ended = datetime(2025, 5, 22, 15, 8, 58)
    ts = TimeStamps(createdAt=created, endedAt=ended)
    assert ts.executionDuration == 1000  # 1 second in milliseconds


def test_execution_duration_none_if_endedAt_missing():
    """Test execution duration is None if endedAt is missing."""
    created = datetime(2025, 5, 22, 15, 8, 57)
    ts = TimeStamps(createdAt=created)
    assert ts.executionDuration is None  # Not enough data to compute


def test_execution_duration_zero_if_same_time():
    """Test execution duration is zero if createdAt and endedAt are the same."""
    t = datetime(2025, 5, 22, 15, 8, 57)
    ts = TimeStamps(createdAt=t, endedAt=t)
    assert ts.executionDuration == 0


def test_runtime_job_model(mock_job_data):
    """Test RuntimeJobModel class."""

    job = RuntimeJobModel.from_dict(mock_job_data)
    assert job.job_id == "job_123"
    assert job.device_id == "device_456"
    assert job.status == JobStatus.COMPLETED
    assert job.shots == 100
    assert isinstance(job.metadata, GateModelExperimentMetadata)
    assert job.time_stamps.executionDuration == 60000  # pylint: disable=no-member

    # Test job with missing metadata
    job_data = mock_job_data.copy()
    job_data.pop("metadata", None)
    job = RuntimeJobModel.from_dict(job_data)
    assert isinstance(job.metadata, GateModelExperimentMetadata)

    with pytest.raises(ValueError):
        RuntimeJobModel.from_dict(
            {"qbraidJobId": "job_123", "qbraidDeviceId": "device_456", "status": "invalid_status"}
        )


def test_populate_metadata(valid_qasm2_no_meas):
    """Test _populate_metadata method."""
    job_data_gm = {"openQasm": valid_qasm2_no_meas, "circuitNumQubits": 5, "circuitDepth": 10}
    populated_data = RuntimeJobModel._populate_metadata(job_data_gm, ExperimentType.GATE_MODEL)
    assert isinstance(populated_data["metadata"], GateModelExperimentMetadata)
    assert populated_data["metadata"].qasm == valid_qasm2_no_meas

    job_data_ahs = {"numAtoms": 10}
    populated_data = RuntimeJobModel._populate_metadata(job_data_ahs, ExperimentType.AHS)
    assert isinstance(populated_data["metadata"], AhsExperimentMetadata)


def test_runtime_job_model_metadata_population():
    """Test metadata population in RuntimeJobModel."""
    job_data = {
        "qbraidJobId": "job_123",
        "qbraidDeviceId": "device_456",
        "status": "CANCELLED",
        "shots": 100,
        "experimentType": "other",
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
        "experimentType": "ahs",
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
    bad_job_data = mock_job_data.copy()
    bad_job_data["experimentType"] = bad_type
    with pytest.raises(ValueError) as excinfo:
        RuntimeJobModel.from_dict(bad_job_data)
    assert str(excinfo.value).startswith(f"'{bad_type}' is not a valid ExperimentType")

    model = RuntimeJobModel.from_dict(mock_job_data)

    with pytest.raises(ValidationError) as excinfo:
        _ = RuntimeJobModel(
            qbraidJobId=model.job_id,
            qbraidDeviceId=model.device_id,
            status=model.status.value,
            statusText=model.status_text,
            shots=model.shots,
            experimentType=bad_type,
            metadata=model.metadata,
            timeStamps=model.time_stamps,
            tags=model.tags,
            cost=model.cost,
        )
    assert f"Invalid experiment_type: '{bad_type}'" in str(excinfo.value)


def test_invalid_status_raises_error(mock_job_data):
    """Test invalid job status raises error."""
    bad_type = "unsupported type"
    bad_job_data = mock_job_data.copy()
    bad_job_data["status"] = bad_type
    with pytest.raises(ValueError) as excinfo:
        RuntimeJobModel.from_dict(bad_job_data)
    assert str(excinfo.value).startswith(f"'{bad_type}' is not a valid JobStatus")

    with pytest.raises(ValidationError) as excinfo:
        RuntimeJobModel(**bad_job_data)
    assert f"Invalid status: '{bad_type}'" in str(excinfo.value)


def test_parse_datetimes_for_none_type(mock_job_data):
    """Test that TimeStamps model can handle None values."""
    time_stamps = mock_job_data["timeStamps"]
    time_stamps["endedAt"] = None
    time_stamps_model = TimeStamps(**time_stamps)
    assert time_stamps_model.endedAt is None


def test_device_data_qir(device_data_qir):
    """Test DeviceData class for qBraid QIR simulator."""
    device = DeviceData(**device_data_qir)

    assert device.provider == "qBraid"
    assert device.name == "QIR sparse simulator"
    assert device.paradigm == "gate-based"
    assert device.device_type == "SIMULATOR"
    assert device.num_qubits == 64
    assert device.pricing.perTask == Decimal("0.005")
    assert device.pricing.perShot == Decimal("0")
    assert device.pricing.perMinute == Decimal("0.075")
    assert device.status == "ONLINE"
    assert device.is_available is True


def test_device_data_quera(device_data_quera):
    """Test DeviceData class for QuEra QASM simulator."""
    device = DeviceData(**device_data_quera)

    assert device.provider == "QuEra"
    assert device.name == "Noisey QASM simulator"
    assert device.paradigm == "gate-based"
    assert device.device_type == "SIMULATOR"
    assert device.num_qubits == 30
    assert device.pricing.perTask == Decimal("0")
    assert device.pricing.perShot == Decimal("0")
    assert device.pricing.perMinute == Decimal("0")
    assert device.status == "ONLINE"
    assert device.is_available is True


def test_device_data_aquila(device_data_aquila):
    """Test DeviceData class for QuEra Aquila QPU."""
    device = DeviceData(**device_data_aquila)

    assert device.provider == "QuEra"
    assert device.name == "Aquila"
    assert device.paradigm == "AHS"
    assert device.device_type == "QPU"
    assert device.num_qubits == 256
    assert device.pricing.perTask == Decimal("0.3")
    assert device.pricing.perShot == Decimal("0.01")
    assert device.pricing.perMinute == Decimal("0")
    assert device.status == "OFFLINE"
    assert device.is_available is False


def test_usd_json_schema():
    """Test JSON schema for USD type."""

    class TestModel(BaseModel):
        """Mock model with USD field."""

        amount: USD

    json_schema = TestModel.model_json_schema()
    amount_schema = json_schema["properties"]["amount"]

    assert amount_schema["title"] == "USD"
    assert amount_schema["description"] == "A monetary amount representing U.S. Dollars."
    assert amount_schema["examples"] == [10, 0.05, 1.5]
    assert amount_schema["type"] == "number"


def test_credits_json_schema():
    """Test JSON schema for Credits type."""

    class TestModel(BaseModel):
        """Mock model with Credits field."""

        amount: Credits

    json_schema = TestModel.model_json_schema()
    amount_schema = json_schema["properties"]["amount"]

    assert amount_schema["title"] == "Credits"
    assert amount_schema["description"] == "A monetary amount where 1 Credit = $0.01 USD."
    assert amount_schema["examples"] == [10, 0.05, 1.5]
    assert amount_schema["type"] == "number"


def test_credits_pydantic_parsing():
    """Test parsing of Credits type in Pydantic models."""

    class TestModel(BaseModel):
        """Mock model with Credits field."""

        amount: Credits

    model_int = TestModel(amount=100)
    assert isinstance(model_int.amount, Credits)
    assert model_int.amount == Credits(100)

    model_float = TestModel(amount=100.5)
    assert isinstance(model_float.amount, Credits)
    assert model_float.amount == Credits(100.5)

    model_decimal = TestModel(amount=Decimal("100.75"))
    assert isinstance(model_decimal.amount, Credits)
    assert model_decimal.amount == Credits(Decimal("100.75"))

    model_str = TestModel(amount="200")
    assert isinstance(model_str.amount, Credits)
    assert model_str.amount == Credits(200)

    with pytest.raises(ValidationError) as excinfo:
        TestModel(amount="invalid")

    assert "Input should be a number (int, float, or Decimal)" in str(excinfo.value)


def test_qubo_solve_params_model():
    """Test QuboSolveParams with valid parameters."""
    params = QuboSolveParams(
        offset=0.5,
        num_reads=10,
        num_results=5,
        num_sweeps=1000,
        beta_range=(5.0, 100.0, 200),
        beta_list=[1.2, 5.5, 10.0],
        dense=True,
        vector_mode="speed",
        timeout=3600,
        ve_num=2,
        onehot=[["x[0]", "x[1]"]],
        fixed={"x[0]": 1, "x[1]": 0},
        andzero=[["x[0]", "x[1]"]],
        orone=[["x[1]", "x[2]"]],
        supplement=[["y[0]", "y[1]"]],
        maxone=[[1, ["x[0]", "x[1]"]]],
        minmaxone=[[1, 2, ["x[1]", "x[2]"]]],
        init_spin={"x[0]": 1, "x[1]": 0},
        spin_list=["x[1]", "x[2]"],
    )
    assert params.num_reads == 10
    assert params.beta_range == (5.0, 100.0, 200)
    assert params.vector_mode == "speed"


def test_qubo_solve_params_invalid_offset():
    """Test QuboSolveParams with an invalid offset value outside of the allowed range."""
    with pytest.raises(ValidationError, match="offset must be between"):
        QuboSolveParams(offset=3.5e40)


def test_qubo_solve_params_invalid_num_reads():
    """Test QuboSolveParams with invalid num_reads outside the range of 1 to 20."""
    with pytest.raises(ValidationError, match="num_reads must be between 1 and 20"):
        QuboSolveParams(offset=0.5, num_reads=25)


def test_qubo_solve_params_invalid_num_sweeps():
    """Test QuboSolveParams with invalid num_sweeps outside the range of 1 to 100000."""
    with pytest.raises(ValidationError, match="num_sweeps must be between 1 and 100000"):
        QuboSolveParams(offset=0.5, num_sweeps=200000)


def test_qubo_solve_params_invalid_beta_range():
    """Test QuboSolveParams with invalid beta_range values."""
    with pytest.raises(ValidationError, match="start value must be between"):
        QuboSolveParams(offset=0.5, beta_range=(1e-40, 100.0, 200))

    with pytest.raises(ValidationError, match="end value must be between"):
        QuboSolveParams(offset=0.5, beta_range=(10.0, 4e40, 200))

    with pytest.raises(
        ValidationError, match="start value must be less than or equal to end value"
    ):
        QuboSolveParams(offset=0.5, beta_range=(200.0, 10.0, 200))

    with pytest.raises(ValidationError, match="steps must be between 1 and 100000"):
        QuboSolveParams(offset=0.5, beta_range=(10.0, 100.0, -2))


def test_qubo_solve_params_invalid_beta_list():
    """Test QuboSolveParams with invalid beta_list values outside the allowed range."""
    with pytest.raises(ValidationError, match="All beta values must be between"):
        QuboSolveParams(offset=0.5, beta_list=[1e-40, 10.0, 5e40])


def test_qubo_solve_params_invalid_timeout():
    """Test QuboSolveParams with an invalid timeout outside the range of 1 to 7200."""
    with pytest.raises(ValidationError, match="timeout must be between 1 and 7200 seconds"):
        QuboSolveParams(offset=0.5, timeout=8000)


def test_qubo_solve_params_invalid_vector_mode():
    """Test QuboSolveParams with an invalid vector_mode value."""
    with pytest.raises(ValidationError, match="vector_mode must be 'speed' or 'accuracy'"):
        QuboSolveParams(offset=0.5, vector_mode="fast")


def test_qubo_solve_params_invalid_ve_num():
    """Test QuboSolveParams with invalid ve_num below 1."""
    with pytest.raises(ValidationError, match="ve_num must be greater than or equal to 1"):
        QuboSolveParams(offset=0.5, ve_num=0)


def test_qubo_solve_params_beta_list_none():
    """Test QuboSolveParams beta_list set to None."""
    params = QuboSolveParams(offset=0.5, beta_list=None)
    assert params.beta_list is None


def test_device_pricing():
    """Test DevicePricing class."""
    pricing = DevicePricing(
        perTask=USD(0.5),
        perShot=USD(0.01),
        perMinute=USD(0.075),
    )
    assert pricing.perTask == USD(0.5)
    assert pricing.perShot == USD(0.01)
    assert pricing.perMinute == USD(0.075)

    pricing_credits = pricing.serialize_credits(pricing.perTask)
    assert isinstance(pricing_credits, Credits)
    assert pricing_credits == Credits(50)


@pytest.mark.parametrize(
    "sites, expected",
    [
        ([(1.0, 2.0), (3.0, 4.0)], [(1.0, 2.0), (3.0, 4.0)]),
        ([(1, 2), (3, 4)], [(1.0, 2.0), (3.0, 4.0)]),
        (None, None),
        ([], []),
    ],
)
def test_ahs_expt_validate_sites_valid(sites, expected):
    """Test AhsExperimentMetadata sites validation."""
    model = AhsExperimentMetadata(sites=sites)
    assert model.sites == expected


@pytest.mark.parametrize(
    "sites",
    [
        [(1, 2, 3)],
        [(1,)],
        [1, 2],
        ["a", "b"],
        [("a", "b")],
        "not a list",
        [("1.0", "2.0"), ("3.0", "not_a_number")],
        [(1, 2, 3), (4, 5)],
        [(1, 2), "not_a_tuple"],
    ],
)
def test_ahs_expt_validate_sites_invalid(sites):
    """Test raising ValidationError for invalid sites."""
    with pytest.raises(ValidationError):
        AhsExperimentMetadata(sites=sites)


def test_ahs_expt_sites_lists_to_tuples():
    """Test AhsExperimentMetadata sites lists converted to tuples."""
    model = AhsExperimentMetadata(sites=[[1, 2], [3, 4]])
    assert model.sites == [(1.0, 2.0), (3.0, 4.0)]


def test_ahs_expt_measurement_counts_dict_to_counter():
    """Test AhsExperimentMetadata measurement_counts dict converted to Counter."""
    model = AhsExperimentMetadata(measurementCounts={"ggrggrgg": 1, "rgggrggg": 1})
    assert model.measurement_counts == Counter({"ggrggrgg": 1, "rgggrggg": 1})


@pytest.mark.parametrize(
    "filling, expected",
    [
        ([0, 1, 0, 1], [0, 1, 0, 1]),
        ([True, False, True], [1, 0, 1]),
        (None, None),
        ([], []),
    ],
)
def test_ahs_expt_validate_filling_valid(filling, expected):
    """Test AhsExperimentMetadata filling validation."""
    model = AhsExperimentMetadata(filling=filling)
    assert model.filling == expected


@pytest.mark.parametrize(
    "filling",
    [[0, 1, 2], [0, 1, -1], [0.5, 1.5], "not a list"],
)
def test_ahs_expt_validate_filling_invalid(filling):
    """Test raising ValidationError for invalid filling."""
    with pytest.raises(ValidationError):
        AhsExperimentMetadata(filling=filling)


def test_ahs_expt_validate_infer_num_atoms():
    """Test inferring num_atoms from sites and filling."""
    model = AhsExperimentMetadata(sites=[(0, 0), (1, 1), (2, 2)], filling=[0, 1, 0])
    assert model.num_atoms == 3


def test_ahs_expt_validate_sites_filling_mismatch():
    """Test raising ValidationError for sites and filling length mismatch."""
    with pytest.raises(
        ValidationError,
        match="The lengths of 'sites', 'filling', and value of 'num_atoms' must be consistent.",
    ):
        AhsExperimentMetadata(sites=[(0, 0), (1, 1)], filling=[0, 1, 0])


def test_ahs_expt_validate_num_atoms_mismatch():
    """Test raising ValidationError for num_atoms mismatch."""
    with pytest.raises(
        ValidationError,
        match="The lengths of 'sites', 'filling', and value of 'num_atoms' must be consistent.",
    ):
        AhsExperimentMetadata(sites=[(0, 0), (1, 1)], filling=[0, 1], numAtoms=3)


@pytest.mark.parametrize(
    "sites, filling",
    [
        ([(0, 0), (1, 1)], None),
        (None, [0, 1]),
    ],
)
def test_ahs_expt_validate_partial_data(sites, filling):
    """Test AhsExperimentMetadata with partial data."""
    model = AhsExperimentMetadata(sites=sites, filling=filling)
    assert model.num_atoms == 2


def test_ahs_expt_validate_empty_lists():
    """Test AhsExperimentMetadata with empty lists."""
    model = AhsExperimentMetadata(sites=[], filling=[])
    assert model.num_atoms is None

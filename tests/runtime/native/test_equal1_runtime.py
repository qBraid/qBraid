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
Unit tests for Equal1 simulator runtime through native provider.

"""
import pytest

from qbraid.programs import ExperimentType
from qbraid.runtime import JobStatus, Result
from qbraid.runtime.native.result import Equal1SimulatorResultData
from qbraid.runtime.schemas import RuntimeJobModel
from qbraid.runtime.schemas.experiment import Equal1SimulationMetadata


@pytest.fixture
def equal1_partial_base64_data():
    """Fixture providing the partial base64 encoded compiled output."""
    return "T1BFTlFBU00gMi4wOwppbmNsdWRlICJxZWxpYjEuaW5jIjsKcXJlZyBxWzZdOwpjcmVnIG1lYXNbMl07"


@pytest.fixture
def equal1_full_base64_data():
    """Fixture providing the complete base64 encoded compiled output."""
    return (
        "T1BFTlFBU00gMi4wOwppbmNsdWRlICJxZWxpYjEuaW5jIjsKcXJlZyBxWzZdOwpjcmVnIG1lYXNbMl07"
        "CnJ6KHBpLzIpIHFbMl07CnJ4KHBpLzIpIHFbMl07CnJ6KHBpLzIpIHFbMl07CnJ6KHBpLzIpIHFbM107"
        "CnJ4KHBpLzIpIHFbM107CnJ6KHBpKSBxWzNdOwpjeiBxWzJdLHFbM107CnJ4KHBpLzIpIHFbM107"
        "CnJ6KHBpLzIpIHFbM107CmJhcnJpZXIgcVsyXSxxWzNdOwptZWFzdXJlIHFbMl0gLT4gbWVhc1swXTsK"
        "bWVhc3VyZSBxWzNdIC0+IG1lYXNbMV07"
    )


@pytest.fixture
def equal1_partial_decoded_qasm():
    """Fixture providing the expected decoded partial compiled output."""
    return 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[6];\ncreg meas[2];'


@pytest.fixture
def equal1_full_decoded_qasm():
    """Fixture providing the expected decoded complete compiled output."""
    return """OPENQASM 2.0;
include "qelib1.inc";
qreg q[6];
creg meas[2];
rz(pi/2) q[2];
rx(pi/2) q[2];
rz(pi/2) q[2];
rz(pi/2) q[3];
rx(pi/2) q[3];
rz(pi) q[3];
cz q[2],q[3];
rx(pi/2) q[3];
rz(pi/2) q[3];
barrier q[2],q[3];
measure q[2] -> meas[0];
measure q[3] -> meas[1];"""


@pytest.fixture
def equal1_partial_data(equal1_partial_base64_data):
    """Fixture providing partial Equal1 simulation metadata fields."""
    return {
        "compiledOutput": equal1_partial_base64_data,
        "irType": "qasm2",
        "noiseModel": "bell1-6",
    }


@pytest.fixture
def equal1_full_data(equal1_partial_data):
    """Fixture providing complete Equal1 simulation metadata example data."""
    return {
        **equal1_partial_data,
        "simulationPlatform": "CPU",
        "simulationMode": None,
        "executionOptions": {"force_bypass_transpilation": 0, "optimization_level": 3},
    }


@pytest.fixture
def equal1_data_with_qasm(equal1_partial_data):
    """Fixture providing Equal1 data with QASM and measurement counts."""
    qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""
    return {
        **equal1_partial_data,
        "openQasm": qasm,
        "measurementCounts": {"00": 100, "11": 100},
    }


@pytest.fixture
def equal1_expected_decoded(equal1_partial_decoded_qasm):
    """Fixture providing the expected decoded compiled output."""
    return equal1_partial_decoded_qasm


def test_equal1_simulation_metadata_base64_decoding(
    equal1_full_base64_data, equal1_full_decoded_qasm
):
    """Test that compiled_output is automatically decoded from base64."""
    # Use the correct alias name to match the field definition
    metadata = Equal1SimulationMetadata(compiledOutput=equal1_full_base64_data)
    assert metadata.compiled_output == equal1_full_decoded_qasm

    # Test with None value
    metadata_none = Equal1SimulationMetadata(compiledOutput=None)
    assert metadata_none.compiled_output is None


def test_equal1_simulation_metadata(equal1_full_data, equal1_expected_decoded):
    """Test the Equal1SimulationMetadata class with complete example data."""
    metadata = Equal1SimulationMetadata(**equal1_full_data)

    # compiled_output should be automatically decoded from base64
    assert metadata.compiled_output == equal1_expected_decoded
    assert metadata.ir_type == equal1_full_data["irType"]
    assert metadata.noise_model == equal1_full_data["noiseModel"]
    assert metadata.simulation_platform == equal1_full_data["simulationPlatform"]
    assert metadata.execution_options == equal1_full_data["executionOptions"]

    # Test that the base class fields are accessible (inherited from GateModelExperimentMetadata)
    assert metadata.measurement_counts is None
    assert metadata.measurements is None
    assert metadata.qasm is None
    assert metadata.num_qubits is None
    assert metadata.gate_depth is None


def test_equal1_simulation_metadata_partial(equal1_partial_data, equal1_expected_decoded):
    """Test Equal1SimulationMetadata with partial data."""
    metadata = Equal1SimulationMetadata(**equal1_partial_data)

    # Test that provided fields are set
    # compiled_output should be automatically decoded from base64
    assert metadata.compiled_output == equal1_expected_decoded
    assert metadata.ir_type == equal1_partial_data["irType"]
    assert metadata.noise_model == equal1_partial_data["noiseModel"]

    # Test that optional fields are None
    assert metadata.simulation_platform is None
    assert metadata.execution_options is None


def test_equal1_simulation_metadata_empty():
    """Test Equal1SimulationMetadata with empty data."""
    metadata = Equal1SimulationMetadata()

    # Test that all fields are None when no data is provided
    assert metadata.compiled_output is None
    assert metadata.ir_type is None
    assert metadata.noise_model is None
    assert metadata.simulation_platform is None
    assert metadata.execution_options is None


def test_equal1_simulation_metadata_with_qasm(equal1_data_with_qasm, equal1_expected_decoded):
    """Test Equal1SimulationMetadata with QASM data to test inheritance."""
    metadata = Equal1SimulationMetadata(**equal1_data_with_qasm)

    # Test Equal1 specific fields
    # compiled_output should be automatically decoded from base64
    assert metadata.compiled_output == equal1_expected_decoded
    assert metadata.ir_type == equal1_data_with_qasm["irType"]
    assert metadata.noise_model == equal1_data_with_qasm["noiseModel"]

    # Test inherited fields
    assert metadata.qasm == equal1_data_with_qasm["openQasm"]
    assert metadata.measurement_counts is not None
    assert metadata.measurement_counts["00"] == 100
    assert metadata.measurement_counts["11"] == 100


def test_equal1_result_with_metadata_and_data():
    """Test getting a Result object with RuntimeJobModel and Equal1SimulatorResultData."""
    device_id = "equal1_simulator"
    job_id = "equal1_simulator-jovyan-qjob-2ht3zyghhxsr8gqbu8yj"
    counts = {"11": 5, "00": 5}
    ir_type = "qasm2"
    noise_model = "ideal"
    simulation_platform = "CPU"
    execution_options = None
    qasm = (
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];'
        "\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];"
    )

    job_data = {
        "timeStamps": {
            "createdAt": "2025-08-28T18:44:45.000Z",
            "endedAt": "2025-08-28T18:44:45.000Z",
            "executionDuration": 72,
        },
        "queuePosition": None,
        "queueDepth": None,
        "measurements": [],
        "prelight": False,
        "circuitNumQubits": 2,
        "circuitDepth": 3,
        "email": "jovyan@example.com",
        "qbraidDeviceId": device_id,
        "qbraidJobId": job_id,
        "status": "COMPLETED",
        "vendor": "qbraid",
        "provider": "equal1",
        "escrow": 0,
        "shots": 10,
        "openQasm": qasm,
        "experimentType": "gate_model",
        "cost": 0.015,
        "measurementCounts": counts,
        "statusText": "",
    }
    job_result = {
        "measurementCounts": counts,
        "qbraidJobId": job_id,
        "status": "COMPLETED",
        "statusText": "",
        "timeStamps": {
            "createdAt": "2025-08-28T18:44:45Z",
            "endedAt": "2025-08-28T18:44:45Z",
            "executionDuration": 72,
        },
        "compiledOutput": (
            "T1BFTlFBU00gMi4wOwppbmNsdWRlICJxZWxpYjEuaW5jIjsKcXJlZyBxWzJdOwpjcmVnIGNbMl07Cmgg"
            "cVswXTsKY3ggcVswXSxxWzFdOwptZWFzdXJlIHFbMF0gLT4gY1swXTsKbWVhc3VyZSBxWzFdIC0+IGNb"
            "MV07"
        ),
        "irType": ir_type,
        "noiseModel": noise_model,
        "simulationPlatform": simulation_platform,
        "executionOptions": execution_options,
    }
    success = job_data.get("status") == JobStatus.COMPLETED.name
    job_result.update(job_data)
    model = RuntimeJobModel.from_dict(job_result)

    data = Equal1SimulatorResultData.from_object(model.metadata)

    exclude = {"measurement_counts", "measurements"}

    metadata_dump = model.metadata.model_dump(by_alias=True, exclude=exclude)
    model_dump = model.model_dump(
        by_alias=True, exclude={"job_id", "device_id", "metadata", "queue_position"}
    )
    experiment_type: ExperimentType = model_dump["experimentType"]

    status_text = model.status_text or model.status.status_message or model.status.default_message
    model_dump.update(
        {
            "status": model.status.name,
            "statusText": status_text,
            "experimentType": experiment_type,
        }
    )
    model_dump["metadata"] = metadata_dump
    result = Result(
        device_id=model.device_id, job_id=model.job_id, success=success, data=data, **model_dump
    )

    # Test the Result object
    assert result.device_id == device_id
    assert result.job_id == job_id
    assert result.success is True

    # Test that metadata fields are accessible via the nested metadata structure
    assert result.details["metadata"]["compiledOutput"] == qasm
    assert result.details["metadata"]["irType"] == ir_type
    assert result.details["metadata"]["noiseModel"] == noise_model
    assert result.details["metadata"]["simulationPlatform"] == simulation_platform
    assert result.details["metadata"]["executionOptions"] == execution_options

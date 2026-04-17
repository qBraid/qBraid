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
from qbraid_core.services.runtime.schemas import Result as CoreResult

from qbraid.programs import ExperimentType
from qbraid.runtime import Result
from qbraid.runtime.result_data import ResultData


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


def test_equal1_result_with_metadata_and_data():
    """Test getting a Result object with core Result and ResultData.from_object."""
    device_id = "qbraid:equal1:sim:bell-1"
    job_id = "qbraid:equal1:sim:bell-1-37f5-qjob-2ht3zyghhxsr8gqbu8yj"
    counts = {"11": 5, "00": 5}
    time_stamps = {
        "createdAt": "2026-01-16T21:33:11.230773Z",
        "endedAt": "2026-01-16T21:33:15.516909Z",
        "executionDuration": 1200,
    }
    cost = "0.0"

    core_result = CoreResult.model_validate(
        {
            "status": "COMPLETED",
            "cost": cost,
            "timeStamps": time_stamps,
            "resultData": {"measurementCounts": counts},
        }
    )
    data = ResultData.from_object(core_result, ExperimentType.GATE_MODEL)

    result = Result(
        device_id=device_id,
        job_id=job_id,
        success=True,
        data=data,
        time_stamps=time_stamps,
        cost=cost,
    )

    # Test the Result object
    assert result.device_id == device_id
    assert result.job_id == job_id
    assert result.success is True

    # Test that result data has counts
    assert result.data.get_counts() == counts

    # Test that time_stamps and cost are passed through in details
    assert result.details.get("time_stamps") == time_stamps
    assert result.details.get("cost") == cost

# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for Equal1 simulator runtime through native provider.

"""
import pytest

from qbraid.runtime.native.result import Equal1SimulatorResultData
from qbraid.runtime.schemas.experiment import Equal1SimulationMetadata


def test_equal1_simulator_result_data():
    """Test the Equal1SimulatorResultData class."""
    compiled_output = (
        "T1BFTlFBU00gMi4wOwppbmNsdWRlICJxZWxpYjEuaW5jIjsKcXJlZyBxWzZdOwpjcmVnIG1lYXNbMl07"
        "CnJ6KHBpLzIpIHFbMl07CnJ4KHBpLzIpIHFbMl07CnJ6KHBpLzIpIHFbMl07CnJ6KHBpLzIpIHFbM107"
        "CnJ4KHBpLzIpIHFbM107CnJ6KHBpKSBxWzNdOwpjeiBxWzJdLHFbM107CnJ4KHBpLzIpIHFbM107"
        "CnJ6KHBpLzIpIHFbM107CmJhcnJpZXIgcVsyXSxxWzNdOwptZWFzdXJlIHFbMl0gLT4gbWVhc1swXTsK"
        "bWVhc3VyZSBxWzNdIC0+IG1lYXNbMV07"
    )
    qasm_expected = """OPENQASM 2.0;
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
    result_data = Equal1SimulatorResultData(compiled_output)
    assert result_data.compiled_output == qasm_expected


@pytest.fixture
def equal1_partial_data():
    """Fixture providing partial Equal1 simulation metadata fields."""
    return {
        "compiledOutput": (
            "T1BFTlFBU00gMi4wOwppbmNsdWRlICJxZWxpYjEuaW5jIjsKcXJlZyBxWzZdOwpjcmVnIG1lYXNbMl07"
        ),
        "executionMode": "simulation",
        "deviceName": "bell1-6-lin",
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


def test_equal1_simulation_metadata(equal1_full_data):
    """Test the Equal1SimulationMetadata class with complete example data."""
    # Create metadata instance
    metadata = Equal1SimulationMetadata(**equal1_full_data)

    # Test that all fields are correctly set
    assert metadata.compiled_output == equal1_full_data["compiledOutput"]
    assert metadata.execution_mode == equal1_full_data["executionMode"]
    assert metadata.device_name == equal1_full_data["deviceName"]
    assert metadata.simulation_platform == equal1_full_data["simulationPlatform"]
    assert metadata.simulation_mode == equal1_full_data["simulationMode"]
    assert metadata.execution_options == equal1_full_data["executionOptions"]

    # Test that the base class fields are accessible (inherited from GateModelExperimentMetadata)
    assert metadata.measurement_counts is None
    assert metadata.measurements is None
    assert metadata.qasm is None
    assert metadata.num_qubits is None
    assert metadata.gate_depth is None


def test_equal1_simulation_metadata_partial(equal1_partial_data):
    """Test Equal1SimulationMetadata with partial data."""
    metadata = Equal1SimulationMetadata(**equal1_partial_data)

    # Test that provided fields are set
    assert metadata.compiled_output == equal1_partial_data["compiledOutput"]
    assert metadata.execution_mode == equal1_partial_data["executionMode"]
    assert metadata.device_name == equal1_partial_data["deviceName"]

    # Test that optional fields are None
    assert metadata.simulation_platform is None
    assert metadata.simulation_mode is None
    assert metadata.execution_options is None


def test_equal1_simulation_metadata_empty():
    """Test Equal1SimulationMetadata with empty data."""
    metadata = Equal1SimulationMetadata()

    # Test that all fields are None when no data is provided
    assert metadata.compiled_output is None
    assert metadata.execution_mode is None
    assert metadata.device_name is None
    assert metadata.simulation_platform is None
    assert metadata.simulation_mode is None
    assert metadata.execution_options is None


def test_equal1_simulation_metadata_with_qasm(equal1_data_with_qasm):
    """Test Equal1SimulationMetadata with QASM data to test inheritance."""
    metadata = Equal1SimulationMetadata(**equal1_data_with_qasm)

    # Test Equal1 specific fields
    assert metadata.compiled_output == equal1_data_with_qasm["compiledOutput"]
    assert metadata.execution_mode == equal1_data_with_qasm["executionMode"]
    assert metadata.device_name == equal1_data_with_qasm["deviceName"]

    # Test inherited fields
    assert metadata.qasm == equal1_data_with_qasm["openQasm"]
    assert metadata.measurement_counts is not None
    assert metadata.measurement_counts["00"] == 100
    assert metadata.measurement_counts["11"] == 100

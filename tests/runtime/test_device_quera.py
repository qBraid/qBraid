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
Unit tests for QuEra QASM simulator device.

"""
import importlib.util
from unittest.mock import PropertyMock, patch

import pytest
from pandas import DataFrame

from qbraid.programs import ExperimentType
from qbraid.runtime import ProgramValidationError, Result, TargetProfile
from qbraid.runtime.native import QbraidDevice, QbraidJob, QbraidProvider
from qbraid.runtime.native.result import QuEraQasmSimulatorResultData

from ._resources import JOB_DATA_QUERA_QASM, RESULTS_DATA_QUERA_QASM


@pytest.fixture
def mock_quera_profile():
    """Mock profile for testing."""
    return TargetProfile(
        device_id="quera_qasm_simulator",
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=30,
        program_spec=QbraidProvider._get_program_spec("qasm2", "quera_qasm_simulator"),
    )


@pytest.fixture
def mock_quera_device(mock_quera_profile, mock_client):
    """Mock QuEra simulator device for testing."""
    return QbraidDevice(profile=mock_quera_profile, client=mock_client)


@pytest.mark.skipif(
    importlib.util.find_spec("flair_visual") is None, reason="flair-visual is not installed"
)
def test_quera_simulator_workflow(mock_provider, cirq_uniform, valid_qasm2_no_meas):
    """Test queara simulator job submission and result retrieval."""
    circuit = cirq_uniform(num_qubits=5, measure=False)
    num_qubits = len(circuit.all_qubits())

    provider = mock_provider
    device = provider.get_device("quera_qasm_simulator")

    shots = 10
    job = device.run(circuit, shots=shots, backend="cirq-gpu")
    assert isinstance(job, QbraidJob)
    assert job.is_terminal_state()
    assert job.queue_position() is None

    device._target_spec = None
    device.prepare = lambda x: {"openQasm": x}
    batch_job = device.run([valid_qasm2_no_meas], shots=shots)
    assert isinstance(batch_job, list)
    assert all(isinstance(job, QbraidJob) for job in batch_job)

    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, QuEraQasmSimulatorResultData)
    assert repr(result.data).startswith("QuEraQasmSimulatorResultData")
    assert result.success
    assert result.job_id == JOB_DATA_QUERA_QASM["qbraidJobId"]
    assert result.device_id == JOB_DATA_QUERA_QASM["qbraidDeviceId"]
    assert result.data.backend == "cirq-gpu"

    counts = result.data.get_counts()
    probabilities = result.data.get_probabilities()
    assert len(counts) == len(probabilities) == 2
    assert sum(probabilities.values()) == 1.0
    assert result.data.measurements is None
    assert (
        result.data.flair_visual_version
        == RESULTS_DATA_QUERA_QASM["quera_simulation_result"]["flair_visual_version"]
    )
    assert result.data.backend == RESULTS_DATA_QUERA_QASM["backend"]

    logs = result.data.get_logs()
    assert isinstance(logs, DataFrame)

    assert result.details["shots"] == shots
    assert result.details["metadata"]["circuitNumQubits"] == num_qubits
    assert isinstance(result.details["timeStamps"]["executionDuration"], int)


def test_validate_quera_device_qasm_validator(mock_quera_device, valid_qasm2):
    """Test that validate method raises ValueError for QASM programs with measurements."""
    with pytest.raises(ProgramValidationError):
        mock_quera_device.validate([valid_qasm2])


def test_construct_aux_payload_no_spec(mock_quera_device, valid_qasm2_no_meas):
    """Test constructing auxiliary payload without a predefined program spec."""
    aux_payload = mock_quera_device._construct_aux_payload(valid_qasm2_no_meas)
    assert len(aux_payload) == 3
    assert aux_payload["openQasm"] == valid_qasm2_no_meas
    assert aux_payload["circuitNumQubits"] == 2
    assert aux_payload["circuitDepth"] == 3


def test_device_validate_emit_warning_for_num_qubits(mock_provider, valid_qasm2_no_meas):
    """Test emitting warning when number of qubits in the circuit exceeds the device capacity."""
    quera_device = mock_provider.get_device("quera_qasm_simulator")
    quera_device._target_spec = None
    quera_device.set_options(validate=1)

    with patch.object(
        type(quera_device), "num_qubits", new_callable=PropertyMock
    ) as mock_num_qubits:
        mock_num_qubits.return_value = 1

        with pytest.warns(
            UserWarning, match=r"Number of qubits in the circuit \(2\) exceeds.*capacity \(1\)"
        ):
            quera_device.validate([valid_qasm2_no_meas])


def test_device_validate_emit_warning_for_target_spec_validator(mock_provider, valid_qasm2):
    """Test emitting warning when target spec validator raises an exception."""
    quera_device = mock_provider.get_device("quera_qasm_simulator")
    quera_device.set_options(validate=1)

    msg = (
        r"OpenQASM programs submitted to the quera_qasm_simulator cannot contain measurement gates"
    )
    with pytest.warns(UserWarning, match=msg):
        quera_device.validate([valid_qasm2])


def test_resolve_noise_model_raises_for_unsupported(mock_quera_device):
    """Test raising exception when no noise models are supported by device."""
    assert mock_quera_device.profile.noise_models is None

    with pytest.raises(ValueError) as excinfo:
        mock_quera_device._resolve_noise_model("ideal")
    assert "Noise models are not supported by this device." in str(excinfo)

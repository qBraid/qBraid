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
Unit tests for submissions to QuEra Aquila device through qBraid native runtime.

"""
import json
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation

from qbraid.programs import ExperimentType
from qbraid.runtime import AhsResultData, Result, TargetProfile
from qbraid.runtime.native import QbraidDevice, QbraidJob, QbraidProvider

from .._resources import JOB_DATA_AQUILA, RESULTS_DATA_AQUILA


@pytest.fixture
def job_data() -> dict[str, Any]:
    """Dictionary of mock QuEra Aquila job data."""
    return JOB_DATA_AQUILA.copy()


@pytest.fixture
def result_data() -> dict[str, Any]:
    """Dictionary of mock QuEra Aquila result data."""
    return RESULTS_DATA_AQUILA.copy()


@pytest.fixture
def device_id(device_data_aquila) -> str:
    """qBraid ID for QuEra Aquila device."""
    return device_data_aquila["qbraid_id"]


@pytest.fixture
def mock_job_id(job_data) -> str:
    """Mock qBraid ID for QuEra Aquila job."""
    return job_data["qbraidJobId"]


@pytest.fixture
def mock_profile(device_id, device_data_aquila) -> TargetProfile:
    """Mock QuEra Aquila TargetProfile for testing."""
    return TargetProfile(
        device_id=device_id,
        simulator=False,
        experiment_type=ExperimentType.AHS,
        num_qubits=device_data_aquila["numberQubits"],
        program_spec=QbraidProvider._get_program_spec("braket_ahs", device_id),
    )


@pytest.fixture
def mock_device(mock_profile, mock_client) -> QbraidDevice:
    """Mock QuEra Aquila QbraidDevice for testing"""
    return QbraidDevice(profile=mock_profile, client=mock_client)


@pytest.fixture
def mock_job(mock_job_id, mock_device, mock_client) -> QbraidJob:
    """Mock QuEra Aquila QbraidJob for testing."""
    return QbraidJob(job_id=mock_job_id, device=mock_device, client=mock_client)


@pytest.fixture
def mock_result_data(result_data) -> AhsResultData:
    """Mock QuEra Aquila AhsResultData for testing."""
    return AhsResultData.from_dict(result_data)


@pytest.fixture
def mock_result(device_id, mock_job_id, mock_result_data) -> Result:
    """Mock QuEra Aquila Result for testing."""
    return Result(device_id=device_id, job_id=mock_job_id, success=True, data=mock_result_data)


def test_get_aquila_device(device_id, mock_provider):
    """Test getting QuEra Aquila device."""
    device = mock_provider.get_device(device_id)
    assert device.id == device_id


def test_prepare_ahs_program(mock_device, braket_ahs, ahs_dict):
    """Test conversion of AHS program to IR."""
    assert mock_device.prepare(braket_ahs) == {"ahs": json.dumps(ahs_dict)}


@pytest.mark.filterwarnings("ignore:Device is not online*:UserWarning")
def test_submit_ahs_job_to_aquila(braket_ahs, mock_device, mock_job_id):
    """Test submitting AHS job to QuEra Aquila device."""
    job = mock_device.run(braket_ahs)
    assert job.id == mock_job_id


def test_get_aquila_job_result(mock_job, mock_result):
    """Test getting QuEra Aquila job result."""
    result = mock_job.result()
    assert result.data.get_counts() == mock_result.data.get_counts()
    assert result.data.measurements == mock_result.data.measurements


@pytest.fixture
def bloqade_program():
    """Create a Bloqade program batch."""
    try:
        # pylint: disable=import-outside-toplevel
        from bloqade.analog import var  # type: ignore
        from bloqade.analog.atom_arrangement import Square  # type: ignore

        # pylint: enable=import-outside-toplevel

        adiabatic_durations = [0.4, 3.2, 0.4]

        max_detuning = var("max_detuning")
        adiabatic_program = (
            Square(3, lattice_spacing="lattice_spacing")
            .rydberg.rabi.amplitude.uniform.piecewise_linear(
                durations=adiabatic_durations, values=[0.0, "max_rabi", "max_rabi", 0.0]
            )
            .detuning.uniform.piecewise_linear(
                durations=adiabatic_durations,
                values=[
                    -max_detuning,
                    -max_detuning,
                    max_detuning,
                    max_detuning,
                ],
            )
            .assign(max_rabi=15.8, max_detuning=16.33)
            .batch_assign(lattice_spacing=np.arange(4.0, 7.0, 1.0))
        )

        return adiabatic_program
    except ImportError as err:
        pytest.skip(f"Bloqade is not installed: {err}")

        return None


def test_device_validate_calls_for_bloqade_run_input(bloqade_program, mock_device: QbraidDevice):
    """Test that validate is called once with a list of AnalogHamiltonianSimulation."""
    mock_device.set_options(validate=0)

    with patch.object(mock_device, "validate", wraps=mock_device.validate) as mock_validate:
        _ = mock_device.run(bloqade_program, shots=10)

        mock_validate.assert_called_once()
        args, _ = mock_validate.call_args
        assert len(args) == 1

        run_input = args[0]
        assert isinstance(run_input, list)
        assert len(run_input) == 3
        assert all(isinstance(program, AnalogHamiltonianSimulation) for program in run_input)


def test_device_to_ir_calls_for_bloqade_run_input(bloqade_program, mock_device: QbraidDevice):
    """Test that to_ir is called three times with AnalogHamiltonianSimulation."""
    mock_device.set_options(validate=0)

    with patch.object(mock_device, "prepare", wraps=mock_device.prepare) as mock_to_ir:
        _ = mock_device.run(bloqade_program, shots=10)

        assert mock_to_ir.call_count == 3
        for call_args in mock_to_ir.call_args_list:
            args, _ = call_args
            assert len(args) == 1
            assert isinstance(args[0], AnalogHamiltonianSimulation)

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

import pytest

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


def test_ahs_program_to_ir(mock_device, braket_ahs, ahs_dict):
    """Test conversion of AHS program to IR."""
    assert mock_device.to_ir(braket_ahs) == {"ahs": json.dumps(ahs_dict)}


def test_submit_ahs_job_to_aquila(braket_ahs, mock_device, mock_job_id):
    """Test submitting AHS job to QuEra Aquila device."""
    job = mock_device.run(braket_ahs)
    assert job.id == mock_job_id


def test_get_aquila_job_result(mock_job, mock_result):
    """Test getting QuEra Aquila job result."""
    result = mock_job.result()
    assert result.data.get_counts() == mock_result.data.get_counts()
    assert result.data.measurements == mock_result.data.measurements

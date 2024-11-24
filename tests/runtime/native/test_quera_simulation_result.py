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
Unit tests for retrieving and post-processing QuEra QASM simulator results.

"""
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError

from qbraid.runtime.native import QbraidJob
from qbraid.runtime.native.result import QuEraQasmSimulatorResultData
from qbraid.runtime.result import Result

try:
    from flair_visual.animation.runtime.qpustate import AnimateQPUState
    from flair_visual.simulation_result import QuEraSimulationResult

    flair_visual_installed = True
except ImportError:
    flair_visual_installed = False


MOCK_JOB_ID = "quera_qasm_simulator-jovyan-qjob-0123456789"


class MockClient:
    """Mock qbraid_core.services.quantum.QuantumClient."""

    def _load_json(self, file_name: str) -> dict[str, Any]:
        """Helper method to load JSON data from a file."""
        file_path = Path(__file__).parent / file_name
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)

    def _get_data_by_job_id(self, file_name: str, job_id: str) -> dict[str, Any]:
        """Helper method to fetch data by job ID from a JSON file."""
        data = self._load_json(file_name)
        if data.get("qbraidJobId") == job_id:
            return data
        raise QuantumServiceRequestError("No jobs found matching the given criteria")

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Mock method to return the metadata corresponding to the specified quantum job."""
        return self._get_data_by_job_id("quera_simulation_data.json", job_id)

    # pylint: disable-next=unused-argument
    def get_job_results(self, job_id: str, **kwargs) -> dict[str, Any]:
        """Mock method to return the results of the quantum job with the given qBraid ID."""
        return self._get_data_by_job_id("quera_simulation_result.json", job_id)


@pytest.fixture
def mock_client() -> MockClient:
    """Fixture for a mock QuantumClient."""
    return MockClient()


@pytest.fixture
def mock_job(mock_client):
    """Fixture for a mock QbraidJob."""
    return QbraidJob(MOCK_JOB_ID, client=mock_client)


@pytest.mark.skipif(not flair_visual_installed, reason="flair-visual is not installed.")
def test_quera_qasm_simulator_job_result(mock_job: QbraidJob):
    """Test processing QuEra QASM simulator job results and result data."""
    result = mock_job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, QuEraQasmSimulatorResultData)

    assert result.data.backend == "cirq-gpu"
    assert result.data.flair_visual_version == "0.5.3"
    assert isinstance(result.data.quera_simulation_result, QuEraSimulationResult)
    assert isinstance(result.data.get_qpu_state(), AnimateQPUState)


@pytest.mark.skipif(not flair_visual_installed, reason="flair-visual is not installed.")
def test_quera_sim_data_get_logs_as_dataframe(mock_job: QbraidJob):
    """Test that get_logs returns the logs as a pandas DataFrame."""
    result = mock_job.result()
    result_data: QuEraQasmSimulatorResultData = result.data
    logs = result_data.get_logs()

    assert isinstance(logs, pd.DataFrame)
    assert logs.shape == (3, 5)  # 3 rows (3 log entries) and 5 columns
    assert list(logs.columns) == ["atom_id", "block_id", "action_type", "time", "duration"]


@pytest.mark.skipif(not flair_visual_installed, reason="flair-visual is not installed.")
def test_quera_sim_data_quera_simulator_result_value_error():
    """Test that get_qpu_state raises ValueError if quera_simulation_result is None."""
    result_data = QuEraQasmSimulatorResultData(backend="cirq", quera_simulation_result=None)

    with pytest.raises(ValueError, match="The simulation result is not available."):
        _ = result_data.quera_simulation_result

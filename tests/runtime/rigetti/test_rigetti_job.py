# Copyright 2026 qBraid
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

# pylint: disable=no-name-in-module,redefined-outer-name,possibly-used-before-assignment,ungrouped-imports

"""Unit tests for RigettiJob."""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from qbraid.runtime import GateModelResultData, Result
from qbraid.runtime.enums import JobStatus

from .conftest import DEVICE_ID, DUMMY_JOB_ID

rigetti_deps_found = (
    importlib.util.find_spec("pyquil") is not None
    and importlib.util.find_spec("qcs_sdk") is not None
)
pytestmark = pytest.mark.skipif(not rigetti_deps_found, reason="Rigetti dependencies not installed")

if rigetti_deps_found:
    from qcs_sdk.qpu.api import QpuApiError

    from qbraid.runtime.rigetti.job import RigettiJob, RigettiJobError

if TYPE_CHECKING:
    from qbraid.runtime.rigetti.device import RigettiDevice


def _make_execution_results(
    readout_data: dict[str, list[int]],
    memory: dict | None = None,
) -> MagicMock:
    """Build a mock ExecutionResults with buffers and memory attributes.

    The new _parse_results approach accesses:
      - execution_results.buffers: dict mapping readout keys to objects with .data attribute
      - execution_results.memory: dict (used as memory_values for QPUResultData)

    Args:
        readout_data: Mapping from readout keys to lists of integer measurement values.
        memory: Optional memory dict (defaults to empty).
    """
    buffers = {}
    for readout_key, values in readout_data.items():
        buf = MagicMock()
        buf.data = values
        buffers[readout_key] = buf

    exec_results = MagicMock()
    exec_results.buffers = buffers
    exec_results.memory = memory if memory is not None else {}
    return exec_results


def _make_simple_execution_results(
    bit_arrays: list[list[int]],
    num_qubits: int | None = None,
) -> tuple[MagicMock, dict[str, str]]:
    """Build execution results for a simple 'ro' register with given shot-level bit arrays.

    Args:
        bit_arrays: List of shots, each shot is a list of bit values.
                    bit_arrays[shot][qubit] = measurement value.
        num_qubits: Number of qubits. If None, inferred from bit_arrays[0].

    Returns:
        (execution_results_mock, ro_sources_dict)
    """
    if num_qubits is None:
        num_qubits = len(bit_arrays[0])
    num_shots = len(bit_arrays)

    ro_sources = {}
    readout_data = {}
    for q in range(num_qubits):
        ref_key = f"ro[{q}]"
        readout_key = f"q{q}_readout"
        ro_sources[ref_key] = readout_key
        # Each readout key gets the values across all shots for that qubit
        readout_data[readout_key] = [bit_arrays[shot][q] for shot in range(num_shots)]

    return _make_execution_results(readout_data), ro_sources


# ===========================================================================
# Job – basic properties
# ===========================================================================


class TestRigettiJobProperties:
    """Tests for RigettiJob internal properties and accessors."""

    def test_job_id_stored_correctly(self, rigetti_job: RigettiJob) -> None:
        """job.id must return the string job ID used at construction."""
        assert rigetti_job.id == DUMMY_JOB_ID

    def test_device_id_matches_device_profile(self, rigetti_job: RigettiJob) -> None:
        """The job's device must carry the correct processor ID."""
        assert rigetti_job._device.id == DEVICE_ID

    def test_client_property_mirrors_device_client(
        self, rigetti_job: RigettiJob, mock_qcs_client: MagicMock
    ) -> None:
        """_client must return the device's _qcs_client."""
        assert rigetti_job._client is mock_qcs_client

    def test_num_shots_stored_correctly(self, rigetti_device: RigettiDevice) -> None:
        """num_shots kwarg must be stored as _num_shots."""
        job = RigettiJob(job_id="x", device=rigetti_device, num_shots=42)
        assert job._num_shots == 42

    def test_num_shots_defaults_to_one(self, rigetti_device: RigettiDevice) -> None:
        """When num_shots is omitted the default must be 1."""
        job = RigettiJob(job_id="x", device=rigetti_device)
        assert job._num_shots == 1

    def test_initial_status_is_initializing(self, rigetti_job: RigettiJob) -> None:
        """A freshly created job must have INITIALIZING status."""
        assert rigetti_job._status == JobStatus.INITIALIZING

    def test_ro_sources_stored_correctly(self, rigetti_device: RigettiDevice) -> None:
        """ro_sources kwarg must be stored as _ro_sources."""
        ro_sources = {"ro[0]": "q0_ro", "ro[1]": "q1_ro"}
        job = RigettiJob(job_id="x", device=rigetti_device, num_shots=1, ro_sources=ro_sources)
        assert job._ro_sources == ro_sources

    def test_ro_sources_defaults_to_empty_dict(self, rigetti_device: RigettiDevice) -> None:
        """When ro_sources is omitted the default must be an empty dict."""
        job = RigettiJob(job_id="x", device=rigetti_device)
        assert job._ro_sources == {}

    def test_execution_duration_microseconds_none_when_no_cached_results(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Property returns None before status()/result() populate _cached_results."""
        job = RigettiJob(job_id="x", device=rigetti_device)
        assert job.execution_duration_microseconds is None

    def test_execution_duration_microseconds_reads_from_cached_results(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Property forwards the cached ExecutionResults attribute."""
        job = RigettiJob(job_id="x", device=rigetti_device)
        cached = MagicMock()
        cached.execution_duration_microseconds = 1_500_000
        job._cached_results = cached
        assert job.execution_duration_microseconds == 1_500_000


# ===========================================================================
# Job – status
# ===========================================================================


class TestRigettiJobStatus:
    """Tests for RigettiJob.status."""

    def test_status_returns_completed_after_successful_retrieval(
        self, rigetti_job: RigettiJob
    ) -> None:
        """status() polls via retrieve_results; a successful call transitions to COMPLETED."""
        exec_results = MagicMock()

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            assert rigetti_job.status() == JobStatus.COMPLETED

    def test_status_passes_correct_args_to_retrieve_results(self, rigetti_job: RigettiJob) -> None:
        """status() must pass job_id, quantum_processor_id, and client to retrieve_results."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=MagicMock(),
        ) as mock_retrieve:
            rigetti_job.status()

        mock_retrieve.assert_called_once_with(
            job_id=str(rigetti_job.id),
            quantum_processor_id=DEVICE_ID,
            client=rigetti_job._client,
            execution_options=rigetti_job._device._execution_options,
        )

    def test_status_reflects_manual_internal_change(self, rigetti_job: RigettiJob) -> None:
        """Changing _status directly must be visible through status()."""
        rigetti_job._status = JobStatus.COMPLETED
        assert rigetti_job.status() == JobStatus.COMPLETED

    def test_status_is_terminal_after_cancel(self, rigetti_job: RigettiJob) -> None:
        """After a successful cancel, status() must be CANCELLED (a terminal state)."""
        with patch("qbraid.runtime.rigetti.job.cancel_job"):
            rigetti_job.cancel()
        assert rigetti_job.status() == JobStatus.CANCELLED
        assert rigetti_job.is_terminal_state()

    def test_status_failed_on_non_timeout_qpu_api_error(self, rigetti_job: RigettiJob) -> None:
        """A non-timeout QpuApiError must transition status to FAILED."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("execution error"),
        ):
            assert rigetti_job.status() == JobStatus.FAILED

    def test_status_unchanged_on_timeout_qpu_api_error(self, rigetti_job: RigettiJob) -> None:
        """A timeout QpuApiError must leave status unchanged (non-terminal)."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("request timeout exceeded"),
        ):
            assert rigetti_job.status() == JobStatus.INITIALIZING


# ===========================================================================
# Job – cancel
# ===========================================================================


class TestRigettiJobCancel:
    """Tests for RigettiJob.cancel."""

    def test_cancel_calls_cancel_job_with_correct_args(
        self, rigetti_job: RigettiJob, mock_qcs_client: MagicMock
    ) -> None:
        """cancel() must forward job_id, quantum_processor_id, and client."""
        with patch("qbraid.runtime.rigetti.job.cancel_job") as mock_cancel:
            rigetti_job.cancel()

        mock_cancel.assert_called_once_with(
            job_id=DUMMY_JOB_ID,
            quantum_processor_id=DEVICE_ID,
            client=mock_qcs_client,
            execution_options=rigetti_job._device._execution_options,
        )

    def test_cancel_sets_status_to_cancelled_on_success(self, rigetti_job: RigettiJob) -> None:
        """A successful cancel must transition status to CANCELLED."""
        with patch("qbraid.runtime.rigetti.job.cancel_job"):
            rigetti_job.cancel()

        assert rigetti_job.status() == JobStatus.CANCELLED

    def test_cancel_transitions_through_cancelling_before_cancelled(
        self, rigetti_job: RigettiJob
    ) -> None:
        """The job must pass through CANCELLING before reaching CANCELLED.

        We capture the status inside cancel_job to verify the intermediate state.
        """
        captured_status_during_call: list[JobStatus] = []

        def _capture_status(*_args, **_kwargs) -> None:
            captured_status_during_call.append(rigetti_job._status)

        with patch("qbraid.runtime.rigetti.job.cancel_job", side_effect=_capture_status):
            rigetti_job.cancel()

        assert captured_status_during_call == [JobStatus.CANCELLING]
        assert rigetti_job.status() == JobStatus.CANCELLED

    def test_cancel_raises_rigetti_job_error_on_qpu_api_error(
        self, rigetti_job: RigettiJob
    ) -> None:
        """A QpuApiError from cancel_job must raise RigettiJobError."""
        with patch(
            "qbraid.runtime.rigetti.job.cancel_job",
            side_effect=QpuApiError("already complete"),
        ):
            with pytest.raises(RigettiJobError, match="cancel"):
                rigetti_job.cancel()

    def test_cancel_status_is_restored_when_qpu_api_error_raised(
        self, rigetti_job: RigettiJob
    ) -> None:
        """When cancel() raises RigettiJobError, the status is restored to pre-cancel state."""
        with patch(
            "qbraid.runtime.rigetti.job.cancel_job",
            side_effect=QpuApiError("already complete"),
        ):
            with pytest.raises(RigettiJobError):
                rigetti_job.cancel()

        assert rigetti_job._status == JobStatus.INITIALIZING

    def test_cancel_non_qpu_api_error_propagates(self, rigetti_job: RigettiJob) -> None:
        """Exceptions other than QpuApiError must not be swallowed."""
        with patch(
            "qbraid.runtime.rigetti.job.cancel_job",
            side_effect=ConnectionError("network failure"),
        ):
            with pytest.raises(ConnectionError, match="network failure"):
                rigetti_job.cancel()


# ===========================================================================
# Job – _build_register_map
# ===========================================================================


class TestRigettiJobBuildRegisterMap:
    """Tests for RigettiJob._build_register_map."""

    def test_build_register_map_returns_register_map(self, rigetti_device: RigettiDevice) -> None:
        """_build_register_map must return a RegisterMap with the declared registers."""
        ro_sources = {"ro[0]": "q0_readout", "ro[1]": "q1_readout"}
        readout_data = {"q0_readout": [0, 1], "q1_readout": [1, 0]}
        exec_results = _make_execution_results(readout_data)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=2, ro_sources=ro_sources
        )
        reg_map = job._build_register_map(exec_results)

        assert "ro" in list(reg_map.keys())

    def test_build_register_map_matrix_shape_matches_shots_and_qubits(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """The register matrix must have shape (num_shots, num_bits_in_register)."""
        ro_sources = {"ro[0]": "q0_ro", "ro[1]": "q1_ro", "ro[2]": "q2_ro"}
        readout_data = {
            "q0_ro": [0, 1, 0, 1],
            "q1_ro": [1, 0, 1, 0],
            "q2_ro": [0, 0, 1, 1],
        }
        exec_results = _make_execution_results(readout_data)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=4, ro_sources=ro_sources
        )
        reg_map = job._build_register_map(exec_results)
        matrix = reg_map.get_register_matrix("ro")
        arr = matrix.to_ndarray()

        assert arr.shape == (4, 3)

    def test_build_register_map_values_are_correct(self, rigetti_device: RigettiDevice) -> None:
        """The register matrix values must match the readout data."""
        ro_sources = {"ro[0]": "q0_ro", "ro[1]": "q1_ro"}
        readout_data = {"q0_ro": [0, 1, 0], "q1_ro": [1, 0, 1]}
        exec_results = _make_execution_results(readout_data)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=3, ro_sources=ro_sources
        )
        reg_map = job._build_register_map(exec_results)
        arr = reg_map.get_register_matrix("ro").to_ndarray()

        expected = np.array([[0, 1], [1, 0], [0, 1]])
        np.testing.assert_array_equal(arr, expected)

    def test_build_register_map_multiple_registers(self, rigetti_device: RigettiDevice) -> None:
        """_build_register_map must handle multiple declared registers."""
        ro_sources = {
            "ro[0]": "r0",
            "aux[0]": "a0",
            "aux[1]": "a1",
        }
        readout_data = {
            "r0": [0, 1],
            "a0": [1, 0],
            "a1": [1, 1],
        }
        exec_results = _make_execution_results(readout_data)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=2, ro_sources=ro_sources
        )
        reg_map = job._build_register_map(exec_results)

        assert "ro" in list(reg_map.keys())
        assert "aux" in list(reg_map.keys())

        ro_arr = reg_map.get_register_matrix("ro").to_ndarray()
        assert ro_arr.shape == (2, 1)

        aux_arr = reg_map.get_register_matrix("aux").to_ndarray()
        assert aux_arr.shape == (2, 2)


# ===========================================================================
# Job – _parse_results
# ===========================================================================


class TestRigettiJobParseResults:
    """Tests for RigettiJob._parse_results using the register map approach."""

    def test_parse_results_raises_when_no_declared_registers(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """When ro_sources is empty, _parse_results must raise RigettiJobError."""
        exec_results = MagicMock()
        exec_results.buffers = {}
        exec_results.memory = {}

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=1)
        # job._ro_sources is {} by default

        with pytest.raises(RigettiJobError, match="No declared registers"):
            job._parse_results(exec_results)

    def test_parse_results_counts_sum_equals_num_shots(self, rigetti_device: RigettiDevice) -> None:
        """Total counts must equal num_shots."""
        num_shots = 4
        bit_arrays = [[0, 1], [1, 0], [0, 1], [1, 1]]
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=num_shots,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        assert sum(result.measurement_counts.values()) == num_shots

    def test_parse_results_measurement_strings_have_correct_length(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Each measurement key must have length == num_qubits (bits per shot)."""
        num_qubits = 5
        bit_arrays = [
            [0, 1, 0, 1, 0],
            [1, 0, 1, 0, 1],
            [0, 0, 1, 1, 0],
        ]
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=3,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        for key in result.measurement_counts:
            assert len(key) == num_qubits

    def test_parse_results_counts_are_correct_for_known_data(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Verify the exact counts produced for a fully known data set."""
        # 3 shots, 2 qubits: [00, 11, 00] -> {"00": 2, "11": 1}
        bit_arrays = [[0, 0], [1, 1], [0, 0]]
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=3,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        assert result.measurement_counts == {"00": 2, "11": 1}

    def test_parse_results_probabilities_sum_to_one(self, rigetti_device: RigettiDevice) -> None:
        """Probabilities must sum to approximately 1.0."""
        bit_arrays = [[0, 1], [1, 0], [0, 1]]
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=3,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        total_prob = sum(result.get_probabilities().values())
        assert abs(total_prob - 1.0) < 1e-9

    def test_parse_results_probabilities_match_counts(self, rigetti_device: RigettiDevice) -> None:
        """Each probability must equal count / total_shots."""
        bit_arrays = [[0, 0], [1, 1], [0, 0]]
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=3,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        for outcome, prob in result.get_probabilities().items():
            expected = result.measurement_counts[outcome] / sum(result.measurement_counts.values())
            assert abs(prob - expected) < 1e-9

    def test_parse_results_single_shot_returns_single_count(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A single-shot result must produce exactly one count of 1."""
        bit_arrays = [[1, 0, 1]]
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=1,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        assert result.measurement_counts == {"101": 1}
        assert result.get_probabilities() == {"101": 1.0}

    def test_parse_results_returns_gate_model_result_data(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """_parse_results must return a GateModelResultData instance."""
        bit_arrays = [[0, 1]]
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=1,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        assert isinstance(result, GateModelResultData)
        assert result.measurement_counts is not None
        assert result.get_probabilities() is not None

    def test_parse_results_multiple_registers_concatenated_in_sorted_order(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """When multiple registers exist, they are concatenated in sorted order."""
        # "aux" comes before "ro" alphabetically, so aux bits come first
        ro_sources = {
            "ro[0]": "r0",
            "aux[0]": "a0",
            "aux[1]": "a1",
        }
        # 2 shots
        readout_data = {
            "r0": [0, 1],
            "a0": [1, 0],
            "a1": [1, 1],
        }
        exec_results = _make_execution_results(readout_data)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=2,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        # Shot 1: aux=[1,1], ro=[0] -> "110"
        # Shot 2: aux=[0,1], ro=[1] -> "011"
        assert result.measurement_counts == {"110": 1, "011": 1}

    def test_parse_results_all_zeros(self, rigetti_device: RigettiDevice) -> None:
        """All-zero measurements must produce a single '000...' count."""
        bit_arrays = [[0, 0], [0, 0], [0, 0]]
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=3,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        assert result.measurement_counts == {"00": 3}

    def test_parse_results_all_ones(self, rigetti_device: RigettiDevice) -> None:
        """All-one measurements must produce a single '111...' count."""
        bit_arrays = [[1, 1], [1, 1]]
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=2,
            ro_sources=ro_sources,
        )
        result = job._parse_results(exec_results)

        assert result.measurement_counts == {"11": 2}


# ===========================================================================
# Job – result (wraps get_result)
# ===========================================================================


class TestRigettiJobResult:
    """Tests for RigettiJob.result -- verifies Result object construction."""

    @staticmethod
    def _make_job_with_results(
        rigetti_device: RigettiDevice,
        bit_arrays: list[list[int]],
    ) -> tuple[RigettiJob, MagicMock]:
        """Create a job and matching execution results for result() testing."""
        exec_results, ro_sources = _make_simple_execution_results(bit_arrays)
        num_shots = len(bit_arrays)

        job = RigettiJob(
            job_id=DUMMY_JOB_ID,
            device=rigetti_device,
            num_shots=num_shots,
            ro_sources=ro_sources,
        )
        return job, exec_results

    def test_result_returns_result_instance(self, rigetti_device: RigettiDevice) -> None:
        """result() must return a qBraid Result object."""
        job, exec_results = self._make_job_with_results(rigetti_device, [[0, 1], [1, 0], [0, 1]])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = job.result()

        assert isinstance(res, Result)

    def test_result_success_true_on_happy_path(self, rigetti_device: RigettiDevice) -> None:
        """result() must report success=True when get_result() does not raise."""
        job, exec_results = self._make_job_with_results(rigetti_device, [[0, 1], [1, 0], [0, 1]])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = job.result()

        assert res.success is True

    def test_result_data_is_gate_model_result_data_on_success(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """On success, result().data must be a GateModelResultData instance."""
        job, exec_results = self._make_job_with_results(rigetti_device, [[0, 1], [1, 0], [0, 1]])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = job.result()

        assert isinstance(res.data, GateModelResultData)

    def test_result_device_id_matches_device_profile(self, rigetti_device: RigettiDevice) -> None:
        """result().device_id must match the device's profile.device_id."""
        job, exec_results = self._make_job_with_results(rigetti_device, [[0, 1]])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = job.result()

        assert res.device_id == DEVICE_ID

    def test_result_job_id_matches_job(self, rigetti_device: RigettiDevice) -> None:
        """result().job_id must match the RigettiJob's own job ID."""
        job, exec_results = self._make_job_with_results(rigetti_device, [[0, 1]])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = job.result()

        assert res.job_id == DUMMY_JOB_ID

    def test_result_sets_status_to_completed_on_success(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A successful result() call must leave the job in COMPLETED state."""
        job, exec_results = self._make_job_with_results(rigetti_device, [[0, 1], [1, 0], [0, 1]])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            job.result()

        assert job.status() == JobStatus.COMPLETED

    def test_result_measurement_counts_stored_correctly(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """The GateModelResultData inside result() must carry the counts."""
        # 3 shots x 2 qubits: [00, 11, 00] -> {"00": 2, "11": 1}
        job, exec_results = self._make_job_with_results(rigetti_device, [[0, 0], [1, 1], [0, 0]])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = job.result()

        assert res.data.measurement_counts == {"00": 2, "11": 1}

    def test_result_passes_correct_args_to_retrieve_results(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """result() must pass job_id, quantum_processor_id, and client to retrieve_results."""
        job, exec_results = self._make_job_with_results(rigetti_device, [[0, 1]])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ) as mock_retrieve:
            job.result()

        mock_retrieve.assert_called_with(
            job_id=str(DUMMY_JOB_ID),
            quantum_processor_id=DEVICE_ID,
            client=job._client,
            execution_options=rigetti_device._execution_options,
        )

    def test_result_raises_on_qpu_api_error(self, rigetti_job: RigettiJob) -> None:
        """A QpuApiError from retrieve_results must propagate (not be caught)."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("QPU unreachable"),
        ):
            with pytest.raises(QpuApiError, match="QPU unreachable"):
                rigetti_job.result()

    def test_result_raises_on_rigetti_job_error_when_no_ro_sources(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A RigettiJobError (no declared registers) must propagate."""
        exec_results = MagicMock()
        exec_results.buffers = {}
        exec_results.memory = {}

        # Create job WITHOUT ro_sources to trigger the error
        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=1)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            with pytest.raises(RigettiJobError, match="No declared registers"):
                job.result()

    def test_result_raises_on_retrieval_failure(self, rigetti_job: RigettiJob) -> None:
        """On retrieval failure, result() must raise rather than return a Result."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("error"),
        ):
            with pytest.raises(QpuApiError):
                rigetti_job.result()

    def test_result_status_failed_on_qpu_api_error(self, rigetti_job: RigettiJob) -> None:
        """A non-timeout retrieval error must transition the job status to FAILED."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("execution error"),
        ):
            with pytest.raises(QpuApiError):
                rigetti_job.result()

        assert rigetti_job._status == JobStatus.FAILED

    def test_result_preserves_device_reference_on_failure(self, rigetti_job: RigettiJob) -> None:
        """On failure, the job's device reference must remain intact."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("error"),
        ):
            with pytest.raises(QpuApiError):
                rigetti_job.result()

        assert rigetti_job._device.id == DEVICE_ID

    def test_result_preserves_job_id_on_failure(self, rigetti_job: RigettiJob) -> None:
        """On failure, the job's ID must remain intact."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("error"),
        ):
            with pytest.raises(QpuApiError):
                rigetti_job.result()

        assert rigetti_job.id == DUMMY_JOB_ID


# ===========================================================================
# Job – repr
# ===========================================================================


def test_rigetti_job_repr(rigetti_job: RigettiJob) -> None:
    """__repr__ must mention the class name and the job ID."""
    r = repr(rigetti_job)
    assert "RigettiJob" in r
    assert DUMMY_JOB_ID in r

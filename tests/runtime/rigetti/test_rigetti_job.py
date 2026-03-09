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

# pylint: disable=redefined-outer-name

"""Unit tests for RigettiJob."""

from __future__ import annotations

import importlib.util
import warnings
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from qbraid.runtime import GateModelResultData, Result
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.rigetti.job import RigettiJob, RigettiJobError

from .conftest import DEVICE_ID, DUMMY_JOB_ID

pyquil_found = importlib.util.find_spec("pyquil") is not None
pytestmark = pytest.mark.skipif(not pyquil_found, reason="pyquil not installed")

if pyquil_found:
    # only import if pyquil is available as python 3.13 does not support pyquil and
    # we want to avoid import errors
    from qcs_sdk.qpu.api import QpuApiError

if TYPE_CHECKING:
    from qbraid.runtime.rigetti.device import RigettiDevice

# ===========================================================================
# Job – basic properties
# ===========================================================================


class TestRigettiJobProperties:
    """Tests for RigettiJob internal properties and accessors."""

    def test_job_id_stored_correctly(self, rigetti_job: RigettiJob) -> None:
        """job.id must return the string job ID used at construction."""
        assert rigetti_job.id == DUMMY_JOB_ID

    def test_quantum_processor_id_matches_device_profile(self, rigetti_job: RigettiJob) -> None:
        """_quantum_processor_id must mirror the device's profile.device_id."""
        assert rigetti_job._quantum_processor_id == DEVICE_ID

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

    def test_initial_status_is_running(self, rigetti_job: RigettiJob) -> None:
        """A freshly created job must have RUNNING status."""
        assert rigetti_job.status() == JobStatus.RUNNING


# ===========================================================================
# Job – status
# ===========================================================================


class TestRigettiJobStatus:
    """Tests for RigettiJob.status."""

    def test_status_returns_current_internal_status(self, rigetti_job: RigettiJob) -> None:
        """status() is a direct read of _status; no network call is made."""
        assert rigetti_job.status() == JobStatus.RUNNING

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

    def test_cancel_reverts_to_running_and_warns_on_qpu_api_error(
        self, rigetti_job: RigettiJob
    ) -> None:
        """A QpuApiError from cancel_job must revert status to RUNNING and emit a warning."""
        with patch(
            "qbraid.runtime.rigetti.job.cancel_job",
            side_effect=QpuApiError("already complete"),
        ):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                rigetti_job.cancel()

        assert rigetti_job.status() == JobStatus.RUNNING
        assert len(caught) == 1
        warning_message = str(caught[0].message)
        assert "cancel" in warning_message.lower() or "cancel" in warning_message

    def test_cancel_warning_is_user_warning(self, rigetti_job: RigettiJob) -> None:
        """The warning emitted on cancellation failure must be a UserWarning."""
        with patch(
            "qbraid.runtime.rigetti.job.cancel_job",
            side_effect=QpuApiError("already complete"),
        ):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                rigetti_job.cancel()

        assert len(caught) == 1
        assert issubclass(caught[0].category, UserWarning)

    def test_cancel_non_qpu_api_error_propagates(self, rigetti_job: RigettiJob) -> None:
        """Exceptions other than QpuApiError must not be swallowed."""
        with patch(
            "qbraid.runtime.rigetti.job.cancel_job",
            side_effect=ConnectionError("network failure"),
        ):
            with pytest.raises(ConnectionError, match="network failure"):
                rigetti_job.cancel()


# ===========================================================================
# Job – get_result (raw data parsing)
# ===========================================================================


class TestRigettiJobGetResult:
    """Tests for RigettiJob.get_result – covers the flat-binary-to-counts conversion."""

    def _make_execution_results(self, flat_binary: list[int]) -> MagicMock:
        """
        Build a mock ExecutionResults object whose .memory['ro'].to_binary()
        returns the given flat binary list.
        """
        ro_memory = MagicMock()
        ro_memory.to_binary.return_value = flat_binary

        exec_results = MagicMock()
        exec_results.memory = {"ro": ro_memory}
        return exec_results

    def test_get_result_calls_retrieve_results_with_correct_args(
        self, rigetti_job: RigettiJob, mock_qcs_client: MagicMock
    ) -> None:
        """get_result must forward job_id, processor_id, and client to retrieve_results."""
        exec_results = self._make_execution_results([0, 1, 1, 0, 1, 1])  # 3 shots × 2 qubits

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ) as mock_retrieve:
            rigetti_job.get_result()

        mock_retrieve.assert_called_once_with(
            job_id=DUMMY_JOB_ID,
            quantum_processor_id=DEVICE_ID,
            client=mock_qcs_client,
        )

    def test_get_result_raises_when_ro_register_absent(self, rigetti_device: RigettiDevice) -> None:
        """A missing 'ro' key in memory must raise RigettiJobError."""
        exec_results = MagicMock()
        exec_results.memory = {}  # no 'ro' key

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=1)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            with pytest.raises(RigettiJobError, match="'ro' register"):
                job.get_result()

    def test_get_result_counts_sum_equals_num_shots(self, rigetti_device: RigettiDevice) -> None:
        """Total counts must equal num_shots."""
        # 4 shots × 2 qubits → flat list of 8 ints
        flat = [0, 1, 1, 0, 0, 1, 1, 1]  # "01","10","01","11"
        exec_results = self._make_execution_results(flat)

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=4)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            result = job.get_result()

        assert sum(result["counts"].values()) == 4

    def test_get_result_measurement_strings_have_correct_length(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Each measurement key must have length == num_qubits (bits per shot).

        The flat list contains only 0/1 values because str(b) is called on each
        element; non-binary integers would produce multi-character strings and
        corrupt the key length calculation.
        """
        num_shots = 3
        num_qubits = 5
        # 3 shots × 5 qubits: all-distinct rows so each shot is its own key
        flat = [
            0,
            1,
            0,
            1,
            0,  # shot 0 → "01010"
            1,
            0,
            1,
            0,
            1,  # shot 1 → "10101"
            0,
            0,
            1,
            1,
            0,
        ]  # shot 2 → "00110"
        exec_results = self._make_execution_results(flat)

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=num_shots)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            result = job.get_result()

        for key in result["counts"]:
            assert len(key) == num_qubits

    def test_get_result_counts_are_correct_for_known_flat_list(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Verify the exact counts produced for a fully known flat binary list.

        flat = [0,0, 1,1, 0,0]  with num_shots=3, num_qubits derived as 2
        Expected measurements: ['00', '11', '00'] → {'00': 2, '11': 1}
        """
        flat = [0, 0, 1, 1, 0, 0]
        exec_results = self._make_execution_results(flat)

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=3)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            result = job.get_result()

        assert result["counts"] == {"00": 2, "11": 1}

    def test_get_result_probabilities_sum_to_one(self, rigetti_device: RigettiDevice) -> None:
        """Probabilities must sum to approximately 1.0."""
        flat = [0, 1, 1, 0, 0, 1]  # 3 shots × 2 qubits
        exec_results = self._make_execution_results(flat)

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=3)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            result = job.get_result()

        total_prob = sum(result["probabilities"].values())
        assert abs(total_prob - 1.0) < 1e-9

    def test_get_result_probabilities_match_counts(self, rigetti_device: RigettiDevice) -> None:
        """Each probability must equal count / total_shots."""
        flat = [0, 0, 1, 1, 0, 0]  # 3 shots × 2 qubits: '00','11','00'
        exec_results = self._make_execution_results(flat)

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=3)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            result = job.get_result()

        for outcome, prob in result["probabilities"].items():
            expected = result["counts"][outcome] / sum(result["counts"].values())
            assert abs(prob - expected) < 1e-9

    def test_get_result_single_shot_returns_single_count(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A single-shot result must produce exactly one count of 1."""
        flat = [1, 0, 1]  # 1 shot × 3 qubits → '101'
        exec_results = self._make_execution_results(flat)

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=1)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            result = job.get_result()

        assert result["counts"] == {"101": 1}
        assert result["probabilities"] == {"101": 1.0}

    def test_get_result_returns_counts_and_probabilities_keys(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """The dict returned by get_result must contain exactly 'counts' and 'probabilities'."""
        flat = [0, 1]
        exec_results = self._make_execution_results(flat)

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=1)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            result = job.get_result()

        assert set(result.keys()) == {"counts", "probabilities"}


# ===========================================================================
# Job – result (wraps get_result)
# ===========================================================================


class TestRigettiJobResult:
    """Tests for RigettiJob.result – verifies Result object construction."""

    def _make_execution_results(self, flat_binary: list[int]) -> MagicMock:
        ro_memory = MagicMock()
        ro_memory.to_binary.return_value = flat_binary
        exec_results = MagicMock()
        exec_results.memory = {"ro": ro_memory}
        return exec_results

    def test_result_returns_result_instance(self, rigetti_job: RigettiJob) -> None:
        """result() must return a qBraid Result object."""
        exec_results = self._make_execution_results([0, 1, 1, 0, 0, 1])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = rigetti_job.result()

        assert isinstance(res, Result)

    def test_result_success_true_on_happy_path(self, rigetti_job: RigettiJob) -> None:
        """result() must report success=True when get_result() does not raise."""
        exec_results = self._make_execution_results([0, 1, 1, 0, 0, 1])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = rigetti_job.result()

        assert res.success is True

    def test_result_data_is_gate_model_result_data_on_success(
        self, rigetti_job: RigettiJob
    ) -> None:
        """On success, result().data must be a GateModelResultData instance."""
        exec_results = self._make_execution_results([0, 1, 1, 0, 0, 1])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = rigetti_job.result()

        assert isinstance(res.data, GateModelResultData)

    def test_result_device_id_matches_device_profile(self, rigetti_job: RigettiJob) -> None:
        """result().device_id must match the device's profile.device_id."""
        exec_results = self._make_execution_results([0, 1])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = rigetti_job.result()

        assert res.device_id == DEVICE_ID

    def test_result_job_id_matches_job(self, rigetti_job: RigettiJob) -> None:
        """result().job_id must match the RigettiJob's own job ID."""
        exec_results = self._make_execution_results([0, 1])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = rigetti_job.result()

        assert res.job_id == DUMMY_JOB_ID

    def test_result_sets_status_to_completed_on_success(self, rigetti_job: RigettiJob) -> None:
        """A successful result() call must leave the job in COMPLETED state."""
        exec_results = self._make_execution_results([0, 1, 1, 0, 0, 1])

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            rigetti_job.result()

        assert rigetti_job.status() == JobStatus.COMPLETED

    def test_result_measurement_counts_stored_correctly(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """The GateModelResultData inside result() must carry the counts from get_result()."""
        flat = [0, 0, 1, 1, 0, 0]  # 3 shots × 2 qubits → {'00': 2, '11': 1}
        ro_memory = MagicMock()
        ro_memory.to_binary.return_value = flat
        exec_results = MagicMock()
        exec_results.memory = {"ro": ro_memory}

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=3)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = job.result()

        assert res.data.measurement_counts == {"00": 2, "11": 1}

    def test_result_success_false_on_qpu_api_error(self, rigetti_job: RigettiJob) -> None:
        """A QpuApiError from retrieve_results must yield success=False."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("QPU unreachable"),
        ):
            res = rigetti_job.result()

        assert res.success is False

    def test_result_success_false_on_rigetti_job_error(self, rigetti_device: RigettiDevice) -> None:
        """A RigettiJobError (e.g. missing 'ro' register) must yield success=False."""
        exec_results = MagicMock()
        exec_results.memory = {}  # triggers RigettiJobError inside get_result

        job = RigettiJob(job_id=DUMMY_JOB_ID, device=rigetti_device, num_shots=1)

        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            return_value=exec_results,
        ):
            res = job.result()

        assert res.success is False

    def test_result_data_is_none_on_failure(self, rigetti_job: RigettiJob) -> None:
        """On failure, result().data must be None."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("error"),
        ):
            res = rigetti_job.result()

        assert res.data is None

    def test_result_sets_status_to_failed_on_qpu_api_error(self, rigetti_job: RigettiJob) -> None:
        """A retrieval error must transition the job to FAILED status."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("error"),
        ):
            rigetti_job.result()

        assert rigetti_job.status() == JobStatus.FAILED

    def test_result_device_id_correct_on_failure(self, rigetti_job: RigettiJob) -> None:
        """Even on failure, result().device_id must be set correctly."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("error"),
        ):
            res = rigetti_job.result()

        assert res.device_id == DEVICE_ID

    def test_result_job_id_correct_on_failure(self, rigetti_job: RigettiJob) -> None:
        """Even on failure, result().job_id must be set correctly."""
        with patch(
            "qbraid.runtime.rigetti.job.retrieve_results",
            side_effect=QpuApiError("error"),
        ):
            res = rigetti_job.result()

        assert res.job_id == DUMMY_JOB_ID


# ===========================================================================
# Job – repr
# ===========================================================================


def test_rigetti_job_repr(rigetti_job: RigettiJob) -> None:
    """__repr__ must mention the class name and the job ID."""
    r = repr(rigetti_job)
    assert "RigettiJob" in r
    assert DUMMY_JOB_ID in r

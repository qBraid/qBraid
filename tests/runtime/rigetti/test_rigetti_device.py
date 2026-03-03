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

"""Unit tests for RigettiDevice."""

from unittest.mock import MagicMock, patch

import pyquil
import pytest
from qcs_sdk.qpu.api import SubmissionError
from qcs_sdk.qpu.isa import GetISAError

from qbraid.runtime import TargetProfile
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.rigetti import RigettiDevice, RigettiJob
from qbraid.runtime.rigetti.job import RigettiJobError

from .conftest import DEVICE_ID, DUMMY_JOB_ID

# ===========================================================================
# Device – status
# ===========================================================================


class TestRigettiDeviceStatus:
    """Tests for RigettiDevice.status."""

    def test_status_online_when_get_isa_succeeds(
        self, rigetti_device: RigettiDevice, mock_isa_response: MagicMock
    ) -> None:
        """Device is ONLINE when get_instruction_set_architecture succeeds."""
        with patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ):
            assert rigetti_device.status() == DeviceStatus.ONLINE

    def test_status_offline_when_get_isa_raises_get_isa_error(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Device is OFFLINE when get_instruction_set_architecture raises GetISAError."""
        with patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
            side_effect=GetISAError("QPU offline"),
        ):
            assert rigetti_device.status() == DeviceStatus.OFFLINE

    def test_status_passes_device_id_and_client_to_get_isa(
        self, rigetti_device: RigettiDevice, mock_isa_response: MagicMock
    ) -> None:
        """status() must call get_isa with the device's own processor ID and client."""
        with patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ) as mock_get_isa:
            rigetti_device.status()

        mock_get_isa.assert_called_once_with(
            quantum_processor_id=DEVICE_ID,
            client=rigetti_device._qcs_client,
        )

    def test_status_simulator_always_online_without_get_isa_call(
        self, simulator_profile: TargetProfile, mock_qcs_client: MagicMock
    ) -> None:
        """A simulator device must report ONLINE and skip the ISA network call."""
        device = RigettiDevice(profile=simulator_profile, qcs_client=mock_qcs_client)

        with patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture"
        ) as mock_get_isa:
            result = device.status()

        assert result == DeviceStatus.ONLINE
        mock_get_isa.assert_not_called()

    def test_status_other_exceptions_propagate(self, rigetti_device: RigettiDevice) -> None:
        """Exceptions other than GetISAError must not be caught by status()."""
        with patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError, match="unexpected"):
                rigetti_device.status()


# ===========================================================================
# Device – live_qubits
# ===========================================================================


class TestRigettiDeviceLiveQubits:
    """Tests for RigettiDevice.live_qubits."""

    def test_live_qubits_returns_node_ids(
        self, rigetti_device: RigettiDevice, mock_isa_response: MagicMock
    ) -> None:
        """live_qubits must extract node_id from each ISA architecture node."""
        with patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ):
            qubits = rigetti_device.live_qubits()

        expected = [node.node_id for node in mock_isa_response.architecture.nodes]
        assert qubits == expected

    def test_live_qubits_calls_get_isa_with_correct_args(
        self, rigetti_device: RigettiDevice, mock_isa_response: MagicMock
    ) -> None:
        """live_qubits must forward the processor ID and client to get_isa."""
        with patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ) as mock_get_isa:
            rigetti_device.live_qubits()

        mock_get_isa.assert_called_once_with(
            quantum_processor_id=DEVICE_ID,
            client=rigetti_device._qcs_client,
        )

    def test_live_qubits_empty_when_no_nodes(self, rigetti_device: RigettiDevice) -> None:
        """live_qubits returns an empty list when the ISA has no nodes."""
        isa = MagicMock()
        isa.architecture.nodes = []

        with patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
            return_value=isa,
        ):
            qubits = rigetti_device.live_qubits()

        assert qubits == []

    def test_live_qubits_returns_list_of_ints(self, rigetti_device: RigettiDevice) -> None:
        """Node IDs are returned in the same order as the ISA nodes list."""
        node_ids = [10, 20, 30]
        isa = MagicMock()
        isa.architecture.nodes = [MagicMock(node_id=nid) for nid in node_ids]

        with patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
            return_value=isa,
        ):
            qubits = rigetti_device.live_qubits()

        assert qubits == node_ids


# ===========================================================================
# Device – _submit / submit
# ===========================================================================


class TestRigettiDeviceSubmit:
    """Tests for RigettiDevice._submit and submit."""

    def _make_program(self, shots: int = 3) -> pyquil.Program:
        """Create a minimal native-Quil Program with the given shot count."""
        p = pyquil.Program()
        p.inst(pyquil.gates.RZ(0.5, 0))
        p.inst(pyquil.gates.MEASURE(0, None))
        p.num_shots = shots
        return p

    def test_submit_single_program_returns_rigetti_job(self, rigetti_device: RigettiDevice) -> None:
        """Submitting a single Program must return a single RigettiJob."""
        program = self._make_program(shots=2)

        fake_translation_result = MagicMock()
        fake_translation_result.program = "COMPILED_PROGRAM"

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ),
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ),
        ):
            job = rigetti_device.submit(program)

        assert isinstance(job, RigettiJob)
        assert job.id == DUMMY_JOB_ID

    def test_submit_calls_translate_with_correct_args(self, rigetti_device: RigettiDevice) -> None:
        """_submit must call translate() with the Quil text, num_shots, processor ID, client."""
        program = self._make_program(shots=5)
        fake_translation_result = MagicMock()
        fake_translation_result.program = "COMPILED_PROGRAM"

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ) as mock_translate,
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ),
        ):
            rigetti_device.submit(program)

        mock_translate.assert_called_once_with(
            native_quil=program.out(),
            num_shots=5,
            quantum_processor_id=DEVICE_ID,
            client=rigetti_device._qcs_client,
        )

    def test_submit_calls_qpu_submit_with_compiled_program(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """_submit must pass translation_result.program to qpu_submit."""
        program = self._make_program(shots=1)
        compiled_program = "COMPILED_NATIVE_QUIL"
        fake_translation_result = MagicMock()
        fake_translation_result.program = compiled_program

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ),
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ) as mock_submit,
        ):
            rigetti_device.submit(program)

        mock_submit.assert_called_once_with(
            program=compiled_program,
            patch_values={},
            quantum_processor_id=DEVICE_ID,
            client=rigetti_device._qcs_client,
        )

    def test_submit_raises_rigetti_job_error_on_submission_error(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A SubmissionError from qpu_submit must be wrapped in RigettiJobError."""
        program = self._make_program(shots=1)
        fake_translation_result = MagicMock()
        fake_translation_result.program = "COMPILED_PROGRAM"

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ),
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                side_effect=SubmissionError("QPU not accepting jobs"),
            ),
            pytest.raises(RigettiJobError, match="Failed to submit"),
        ):
            rigetti_device.submit(program)

    def test_submit_job_stores_correct_num_shots(self, rigetti_device: RigettiDevice) -> None:
        """The returned RigettiJob must store the same num_shots as the program."""
        shots = 7
        program = self._make_program(shots=shots)
        fake_translation_result = MagicMock()
        fake_translation_result.program = "COMPILED_PROGRAM"

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ),
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ),
        ):
            job = rigetti_device.submit(program)

        assert job._num_shots == shots

    def test_submit_defaults_num_shots_to_one_when_program_has_none(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """When program.num_shots is falsy, _submit must use 1 as the default."""
        program = pyquil.Program()
        # pyquil.Program().num_shots == 1 by default; force it to 0 to test branch
        program.num_shots = 0

        fake_translation_result = MagicMock()
        fake_translation_result.program = "COMPILED_PROGRAM"

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ) as mock_translate,
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ),
        ):
            job = rigetti_device.submit(program)

        # num_shots=0 is falsy → implementation uses 1
        mock_translate.assert_called_once()
        _, kwargs = mock_translate.call_args
        assert kwargs["num_shots"] == 1
        assert job._num_shots == 1

    def test_submit_list_returns_list_of_jobs(self, rigetti_device: RigettiDevice) -> None:
        """Submitting a list of programs must return a list of RigettiJobs."""
        programs = [self._make_program(shots=1), self._make_program(shots=2)]
        fake_translation_result = MagicMock()
        fake_translation_result.program = "COMPILED_PROGRAM"

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ),
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ),
        ):
            jobs = rigetti_device.submit(programs)

        assert isinstance(jobs, list)
        assert len(jobs) == len(programs)
        for job in jobs:
            assert isinstance(job, RigettiJob)

    def test_submit_list_submits_each_program_independently(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Each program in a batch must be submitted as an independent job."""
        programs = [self._make_program(shots=1), self._make_program(shots=2)]
        fake_translation_result = MagicMock()
        fake_translation_result.program = "COMPILED_PROGRAM"

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ) as mock_translate,
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ) as mock_qpu_submit,
        ):
            rigetti_device.submit(programs)

        assert mock_translate.call_count == len(programs)
        assert mock_qpu_submit.call_count == len(programs)


# ===========================================================================
# Device – repr / str
# ===========================================================================


def test_rigetti_device_str_repr(rigetti_device: RigettiDevice) -> None:
    """str/repr of RigettiDevice must mention the class name and device ID."""
    text = str(rigetti_device)
    assert "RigettiDevice" in text
    assert DEVICE_ID in text

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

"""Unit tests for RigettiDevice."""

from __future__ import annotations

import importlib.util
from unittest.mock import MagicMock, patch

import pytest

from qbraid.runtime import TargetProfile
from qbraid.runtime.enums import DeviceStatus

from .conftest import DEVICE_ID, DUMMY_JOB_ID

rigetti_deps_found = (
    importlib.util.find_spec("pyquil") is not None
    and importlib.util.find_spec("qcs_sdk") is not None
)
pytestmark = pytest.mark.skipif(not rigetti_deps_found, reason="Rigetti dependencies not installed")

if rigetti_deps_found:
    from qcs_sdk.qpu import ListQuantumProcessorsError
    from qcs_sdk.qpu.api import SubmissionError

    from qbraid.runtime.rigetti import RigettiDevice, RigettiJob
    from qbraid.runtime.rigetti.device import RigettiDeviceError
    from qbraid.runtime.rigetti.job import RigettiJobError
else:
    RigettiDevice = None
    RigettiJob = None

# ===========================================================================
# Device – status
# ===========================================================================


class TestRigettiDeviceStatus:
    """Tests for RigettiDevice.status."""

    def test_status_online_when_processor_list_contains_device(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Device is ONLINE when list_quantum_processors includes the device ID."""
        with patch(
            "qbraid.runtime.rigetti.device.list_quantum_processors",
            return_value=[DEVICE_ID, "Lyra-1"],
        ):
            assert rigetti_device.status() == DeviceStatus.ONLINE

    def test_status_offline_when_processor_list_does_not_contain_device(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Device is OFFLINE when list_quantum_processors omits the device ID."""
        with patch(
            "qbraid.runtime.rigetti.device.list_quantum_processors",
            return_value=["Lyra-1", "QVM-1"],
        ):
            assert rigetti_device.status() == DeviceStatus.OFFLINE

    def test_status_calls_list_quantum_processors_with_client(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """status() must call list_quantum_processors with the device client."""
        with patch(
            "qbraid.runtime.rigetti.device.list_quantum_processors",
            return_value=[DEVICE_ID],
        ) as mock_list_qpus:
            rigetti_device.status()

        mock_list_qpus.assert_called_once_with(client=rigetti_device._qcs_client)

    def test_status_simulator_always_online_without_get_isa_call(
        self, simulator_profile: TargetProfile, mock_qcs_client: MagicMock
    ) -> None:
        """A simulator device must report ONLINE and skip the ISA network call."""
        device = RigettiDevice(profile=simulator_profile, qcs_client=mock_qcs_client)

        with patch("qbraid.runtime.rigetti.device.list_quantum_processors") as mock_list_qpus:
            result = device.status()

        assert result == DeviceStatus.ONLINE
        mock_list_qpus.assert_not_called()

    def test_status_other_exceptions_propagate(self, rigetti_device: RigettiDevice) -> None:
        """Exceptions other than ListQuantumProcessorsError must not be caught."""
        with patch(
            "qbraid.runtime.rigetti.device.list_quantum_processors",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError, match="unexpected"):
                rigetti_device.status()

    def test_status_raises_rigetti_device_error_on_list_qpus_error(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """ListQuantumProcessorsError must be wrapped in RigettiDeviceError."""
        with patch(
            "qbraid.runtime.rigetti.device.list_quantum_processors",
            side_effect=ListQuantumProcessorsError("QCS unavailable"),
        ):
            with pytest.raises(
                RigettiDeviceError, match="Failed to retrieve quantum processor list"
            ):
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
# Device – transform
# ===========================================================================


class TestRigettiDeviceTransform:
    """Tests for RigettiDevice.transform (no-op pass-through)."""

    def test_transform_returns_same_program_object(self, rigetti_device: RigettiDevice) -> None:
        """transform() must return the exact same Program instance (no copy)."""
        # pylint: disable=import-outside-toplevel
        import pyquil
        import pyquil.gates

        # pylint: enable=import-outside-toplevel
        program = pyquil.Program()
        program.inst(pyquil.gates.RZ(0.5, 0))
        assert rigetti_device.transform(program) is program

    def test_transform_output_is_pyquil_program(self, rigetti_device: RigettiDevice) -> None:
        """transform() must return a pyquil.Program instance."""
        # pylint: disable=import-outside-toplevel
        import pyquil

        # pylint: enable=import-outside-toplevel
        result = rigetti_device.transform(pyquil.Program())
        assert isinstance(result, pyquil.Program)

    def test_transform_does_not_modify_quil_output(self, rigetti_device: RigettiDevice) -> None:
        """The Quil string produced before and after transform must be identical."""
        # pylint: disable=import-outside-toplevel
        import pyquil
        import pyquil.gates

        # pylint: enable=import-outside-toplevel
        program = pyquil.Program()
        program.inst(pyquil.gates.RZ(1.0, 1))
        program.inst(pyquil.gates.MEASURE(1, None))
        before = program.out()
        rigetti_device.transform(program)
        assert program.out() == before


# ===========================================================================
# Device – _submit / submit
# ===========================================================================


class TestRigettiDeviceSubmit:
    """Tests for RigettiDevice._submit and submit.

    submit() receives a serialized Quil string (the output of ProgramSpec.serialize,
    i.e. program.out()) together with an explicit shots count.  The pyquil.Program
    object is only used here to generate realistic Quil text; it is NOT passed to
    submit() directly.
    """

    def _make_quil(self, shots: int = 3, qubit: int = 0) -> tuple[str, int]:
        """Return (quil_str, shots) for a minimal native-Quil program."""
        # pylint: disable=import-outside-toplevel
        import pyquil
        import pyquil.gates

        # pylint: enable=import-outside-toplevel
        p = pyquil.Program()
        p.inst(pyquil.gates.RZ(0.5, qubit))
        p.inst(pyquil.gates.MEASURE(qubit, None))
        return p.out(), shots

    def test_submit_single_quil_string_returns_rigetti_job(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Submitting a Quil string must return a single RigettiJob."""
        quil_str, shots = self._make_quil(shots=2)
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
            job = rigetti_device.submit(quil_str, shots=shots)

        assert isinstance(job, RigettiJob)
        assert job.id == DUMMY_JOB_ID

    def test_submit_calls_translate_with_correct_args(self, rigetti_device: RigettiDevice) -> None:
        """_submit must call translate() with the Quil text, num_shots, processor ID, client."""
        quil_str, shots = self._make_quil(shots=5)
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
            rigetti_device.submit(quil_str, shots=shots)

        mock_translate.assert_called_once_with(
            native_quil=quil_str,
            num_shots=shots,
            quantum_processor_id=DEVICE_ID,
            client=rigetti_device._qcs_client,
        )

    def test_submit_calls_qpu_submit_with_compiled_program(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """_submit must pass translation_result.program to qpu_submit."""
        quil_str, shots = self._make_quil(shots=1)
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
            rigetti_device.submit(quil_str, shots=shots)

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
        quil_str, shots = self._make_quil(shots=1)
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
            rigetti_device.submit(quil_str, shots=shots)

    def test_submit_job_stores_correct_num_shots(self, rigetti_device: RigettiDevice) -> None:
        """The returned RigettiJob must store the same num_shots passed to submit."""
        shots = 7
        quil_str, _ = self._make_quil(shots=shots)
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
            job = rigetti_device.submit(quil_str, shots=shots)

        assert job._num_shots == shots

    def test_submit_raises_rigetti_job_error_when_shots_not_provided(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """_submit must raise RigettiJobError when shots is not specified."""
        quil_str, _ = self._make_quil()

        with pytest.raises(RigettiJobError, match="shots"):
            rigetti_device.submit(quil_str)

    def test_submit_list_returns_list_of_jobs(self, rigetti_device: RigettiDevice) -> None:
        """Submitting a list of Quil strings must return a list of RigettiJobs."""
        quil_strings = [self._make_quil(shots=3)[0], self._make_quil(shots=3)[0]]
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
            jobs = rigetti_device.submit(quil_strings, shots=3)

        assert isinstance(jobs, list)
        assert len(jobs) == len(quil_strings)
        for job in jobs:
            assert isinstance(job, RigettiJob)

    def test_submit_list_submits_each_program_independently(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Each Quil string in a batch must be submitted as an independent job."""
        quil_strings = [self._make_quil(shots=3, qubit=0)[0], self._make_quil(shots=3, qubit=1)[0]]
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
            rigetti_device.submit(quil_strings, shots=3)

        assert mock_translate.call_count == len(quil_strings)
        assert mock_qpu_submit.call_count == len(quil_strings)
        submitted_quil = [call.kwargs["native_quil"] for call in mock_translate.call_args_list]
        assert submitted_quil[0] != submitted_quil[1]


# ===========================================================================
# Device – repr / str
# ===========================================================================


def test_rigetti_device_str_repr(rigetti_device: RigettiDevice) -> None:
    """str/repr of RigettiDevice must mention the class name and device ID."""
    text = str(rigetti_device)
    assert "RigettiDevice" in text
    assert DEVICE_ID in text

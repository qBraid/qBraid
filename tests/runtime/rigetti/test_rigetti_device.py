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

# pylint: disable=no-name-in-module,redefined-outer-name,possibly-used-before-assignment,ungrouped-imports,protected-access,too-many-lines

"""Unit tests for RigettiDevice."""

from __future__ import annotations

import datetime
import importlib.util
from unittest.mock import MagicMock, patch

import pytest
import requests

from qbraid.runtime.enums import DeviceStatus

from .conftest import DEVICE_ID, DUMMY_JOB_ID

rigetti_deps_found = (
    importlib.util.find_spec("pyquil") is not None
    and importlib.util.find_spec("qcs_sdk") is not None
)
pytestmark = pytest.mark.skipif(not rigetti_deps_found, reason="Rigetti dependencies not installed")

if rigetti_deps_found:
    import pyquil
    import pyquil.gates
    from qcs_sdk.compiler.quilc import CompilerOpts
    from qcs_sdk.qpu import ListQuantumProcessorsError
    from qcs_sdk.qpu.api import SubmissionError
    from qcs_sdk.qpu.translation import TranslationOptions

    from qbraid.runtime.rigetti import RigettiDevice, RigettiJob
    from qbraid.runtime.rigetti.device import RigettiDeviceError
    from qbraid.runtime.rigetti.job import RigettiJobError
else:
    RigettiDevice = None
    RigettiJob = None


# ===========================================================================
# Device – status
# ===========================================================================


# A maintenance calendar with a single fixed window: 2026-06-23 08:00–12:00 UTC.
MAINTENANCE_ICAL = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "PRODID:-//Rigetti//QCS//EN\r\n"
    "BEGIN:VEVENT\r\n"
    "UID:maint-1@qcs.rigetti.com\r\n"
    "SUMMARY:Scheduled Maintenance\r\n"
    "DTSTART:20260623T080000Z\r\n"
    "DTEND:20260623T120000Z\r\n"
    "END:VEVENT\r\n"
    "END:VCALENDAR\r\n"
)


class TestRigettiDeviceStatus:
    """Tests for RigettiDevice.status."""

    def test_status_online_when_listed_and_no_maintenance(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Device is ONLINE when listed and not inside a maintenance window."""
        with (
            patch(
                "qbraid.runtime.rigetti.device.list_quantum_processors",
                return_value=[DEVICE_ID, "Lyra-1"],
            ),
            patch.object(rigetti_device, "_fetch_maintenance_ical", return_value=""),
        ):
            assert rigetti_device.status() == DeviceStatus.ONLINE

    def test_status_unavailable_during_maintenance(self, rigetti_device: RigettiDevice) -> None:
        """Device is UNAVAILABLE when listed but inside a maintenance window."""
        with (
            patch(
                "qbraid.runtime.rigetti.device.list_quantum_processors",
                return_value=[DEVICE_ID],
            ),
            patch.object(rigetti_device, "_fetch_maintenance_ical", return_value=MAINTENANCE_ICAL),
            patch("qbraid.runtime.rigetti.availability.is_in_maintenance", return_value=True),
        ):
            assert rigetti_device.status() == DeviceStatus.UNAVAILABLE

    def test_status_offline_skips_maintenance_check(self, rigetti_device: RigettiDevice) -> None:
        """OFFLINE devices (not in the catalog) must not trigger a calendar lookup."""
        with (
            patch(
                "qbraid.runtime.rigetti.device.list_quantum_processors",
                return_value=["Lyra-1", "QVM-1"],
            ),
            patch.object(rigetti_device, "_fetch_maintenance_ical") as mock_fetch,
            patch("qbraid.runtime.rigetti.availability.is_in_maintenance") as mock_maint,
        ):
            assert rigetti_device.status() == DeviceStatus.OFFLINE
            mock_fetch.assert_not_called()
            mock_maint.assert_not_called()

    def test_status_degrades_to_online_when_calendar_fails(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A calendar fetch/parse failure must not raise; status() falls back to ONLINE."""
        with (
            patch(
                "qbraid.runtime.rigetti.device.list_quantum_processors",
                return_value=[DEVICE_ID],
            ),
            patch.object(
                rigetti_device,
                "_fetch_maintenance_ical",
                side_effect=RigettiDeviceError("calendar service down"),
            ),
        ):
            assert rigetti_device.status() == DeviceStatus.ONLINE

    def test_status_degrades_to_online_when_calendar_parse_fails(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Malformed calendar data (ValueError) must degrade to ONLINE, not raise."""
        with (
            patch(
                "qbraid.runtime.rigetti.device.list_quantum_processors",
                return_value=[DEVICE_ID],
            ),
            patch.object(rigetti_device, "_fetch_maintenance_ical", return_value=MAINTENANCE_ICAL),
            patch(
                "qbraid.runtime.rigetti.availability.is_in_maintenance",
                side_effect=ValueError("malformed iCalendar"),
            ),
        ):
            assert rigetti_device.status() == DeviceStatus.ONLINE

    def test_status_propagates_unexpected_maintenance_error(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """An unexpected error during the maintenance check must not be swallowed."""
        with (
            patch(
                "qbraid.runtime.rigetti.device.list_quantum_processors",
                return_value=[DEVICE_ID],
            ),
            patch.object(rigetti_device, "_fetch_maintenance_ical", return_value=MAINTENANCE_ICAL),
            patch(
                "qbraid.runtime.rigetti.availability.is_in_maintenance",
                side_effect=AttributeError("genuine bug"),
            ),
        ):
            with pytest.raises(AttributeError, match="genuine bug"):
                rigetti_device.status()

    def test_status_calls_list_quantum_processors_with_client(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """status() must call list_quantum_processors with the device client."""
        with (
            patch(
                "qbraid.runtime.rigetti.device.list_quantum_processors",
                return_value=[DEVICE_ID],
            ) as mock_list_qpus,
            patch.object(rigetti_device, "_fetch_maintenance_ical", return_value=""),
        ):
            rigetti_device.status()

        mock_list_qpus.assert_called_once_with(client=rigetti_device.client)

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
# Device – maintenance calendar
# ===========================================================================


class TestRigettiDeviceMaintenance:
    """Tests for the QCS maintenance-calendar integration on the device."""

    def test_maintenance_calendar_builds_request_and_returns_ical(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """maintenance_calendar() must hit /v1/calendars/{id} with a bearer token."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"maintenanceICal": MAINTENANCE_ICAL}
        with patch(
            "qbraid.runtime.rigetti.device.requests.get", return_value=mock_response
        ) as mock_get:
            result = rigetti_device.maintenance_calendar()

        assert result == MAINTENANCE_ICAL
        url = mock_get.call_args.args[0]
        headers = mock_get.call_args.kwargs["headers"]
        assert url == f"https://api.qcs.rigetti.com/v1/calendars/{DEVICE_ID}"
        assert headers["Authorization"] == "Bearer test-access-token"
        assert mock_get.call_args.kwargs.get("timeout") is not None
        mock_response.raise_for_status.assert_called_once()

    def test_maintenance_calendar_empty_when_field_absent(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A response without maintenanceICal yields an empty string."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        with patch("qbraid.runtime.rigetti.device.requests.get", return_value=mock_response):
            assert rigetti_device.maintenance_calendar() == ""

    def test_maintenance_calendar_wraps_http_error(self, rigetti_device: RigettiDevice) -> None:
        """A failed QCS request must be wrapped in RigettiDeviceError."""
        with patch(
            "qbraid.runtime.rigetti.device.requests.get",
            side_effect=requests.RequestException("boom"),
        ):
            with pytest.raises(RigettiDeviceError, match="Failed to fetch maintenance calendar"):
                rigetti_device.maintenance_calendar()

    def test_availability_window_delegates_to_availability(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """availability_window() must delegate to availability.next_available_time(self)."""
        sentinel = (
            False,
            "01:30:00",
            datetime.datetime(2026, 6, 23, 12, 0, tzinfo=datetime.timezone.utc),
        )
        with patch(
            "qbraid.runtime.rigetti.availability.next_available_time", return_value=sentinel
        ) as mock_next:
            assert rigetti_device.availability_window() == sentinel
        mock_next.assert_called_once_with(rigetti_device)


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
            client=rigetti_device.client,
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


def _mock_compile_pipeline(compiled_quil: str = "COMPILED_QUIL"):
    """Return a fake compilation result whose .program.to_quil() returns *compiled_quil*."""
    mock_compilation_program = MagicMock()
    mock_compilation_program.to_quil.return_value = compiled_quil
    fake_compilation_result = MagicMock()
    fake_compilation_result.program = mock_compilation_program
    return fake_compilation_result


class TestRigettiDeviceTransform:
    """Tests for RigettiDevice.transform (compilation only).

    Per the QuantumDevice.transform contract, the input/output type must
    match. RigettiDevice.transform accepts a pyquil.Program and returns
    a pyquil.Program. Quil-string lowering happens in ProgramSpec.serialize
    (configured by the provider), not in transform.
    """

    def test_transform_program_serializes_before_compile(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """transform(Program) must call program.out() and pass the string to compile_program."""
        # pylint: disable=import-outside-toplevel
        import pyquil
        import pyquil.gates

        # pylint: enable=import-outside-toplevel
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))
        expected_quil_str = program.out()
        fake_comp = _mock_compile_pipeline()

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.TargetDevice.from_isa",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ) as mock_compile,
        ):
            rigetti_device.transform(program)

        mock_compile.assert_called_once()
        assert mock_compile.call_args.kwargs["quil"] == expected_quil_str

    def test_transform_program_returns_program(self, rigetti_device: RigettiDevice) -> None:
        """transform(Program) must return a pyquil.Program."""
        # pylint: disable=import-outside-toplevel
        import pyquil
        import pyquil.gates

        # pylint: enable=import-outside-toplevel
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))
        compiled_quil = "RZ(pi/2) 0\nMEASURE 0 ro[0]\n"
        fake_comp = _mock_compile_pipeline(compiled_quil=compiled_quil)

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.TargetDevice.from_isa",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ),
        ):
            result = rigetti_device.transform(program)

        assert isinstance(result, pyquil.Program)

    def test_transform_compilation_failure_raises_device_error(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A compilation failure must be wrapped in RigettiDeviceError."""
        # pylint: disable=import-outside-toplevel
        import pyquil
        import pyquil.gates

        # pylint: enable=import-outside-toplevel
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                side_effect=RuntimeError("ISA unavailable"),
            ),
            pytest.raises(RigettiDeviceError, match="Compilation failed"),
        ):
            rigetti_device.transform(program)

    def test_transform_raises_when_quilc_unreachable(self, rigetti_device: RigettiDevice) -> None:
        """transform() must fail fast with RigettiDeviceError if quilc is unreachable."""
        # pylint: disable=import-outside-toplevel
        import pyquil
        import pyquil.gates

        # pylint: enable=import-outside-toplevel
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))

        with (
            patch(
                "qbraid.runtime.rigetti.device.socket.create_connection",
                side_effect=OSError("connection refused"),
            ),
            patch("qbraid.runtime.rigetti.device.compile_program") as mock_compile,
            pytest.raises(RigettiDeviceError, match="quilc not reachable"),
        ):
            rigetti_device.transform(program)

        mock_compile.assert_not_called()

    def test_transform_quilc_probe_skipped_for_malformed_url(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A malformed quilc URL (no host/port) skips the probe rather than raising."""
        # pylint: disable=import-outside-toplevel
        import pyquil
        import pyquil.gates

        # pylint: enable=import-outside-toplevel
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))
        rigetti_device.client.quilc_url = "not-a-real-url"
        fake_comp = _mock_compile_pipeline()

        with (
            patch(
                "qbraid.runtime.rigetti.device.socket.create_connection",
            ) as mock_connect,
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.TargetDevice.from_isa",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ),
        ):
            rigetti_device.transform(program)

        mock_connect.assert_not_called()


# ===========================================================================
# Helper: mock the _submit pipeline (transform + qpu_submit)
# ===========================================================================


def _mock_submit_pipeline(
    rigetti_device: RigettiDevice,
    quil_str: str,
    shots: int,
    ro_sources: dict | None = None,
    execution_options=None,
):
    """Patch translate and qpu_submit, then call submit.

    _submit() does NOT call transform(); the parent pipeline handles that.
    Returns (job, mock_translate, mock_qpu_submit).
    """
    if ro_sources is None:
        ro_sources = {"ro[0]": "q0_readout"}

    fake_translation_result = MagicMock()
    fake_translation_result.program = "TRANSLATED_BINARY"
    fake_translation_result.ro_sources = ro_sources

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
        job = rigetti_device.submit(quil_str, shots=shots, execution_options=execution_options)

    return job, mock_translate, mock_qpu_submit


# ===========================================================================
# Device – _submit / submit
# ===========================================================================


class TestRigettiDeviceSubmit:
    """Tests for RigettiDevice._submit and submit.

    submit() receives a serialized Quil string (the output of ProgramSpec.serialize,
    i.e. program.out()) together with an explicit shots count.  The _submit method
    calls translate, then qpu_submit.  Compilation (transform) is handled by the
    parent pipeline before _submit is called.
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
        job, _, _ = _mock_submit_pipeline(rigetti_device, quil_str, shots)

        assert isinstance(job, RigettiJob)
        assert job.id == DUMMY_JOB_ID

    def test_submit_calls_translate_with_quil_and_shots(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """_submit must call translate() with the Quil string and shots."""
        quil_str, shots = self._make_quil(shots=10)
        _, mock_translate, _ = _mock_submit_pipeline(rigetti_device, quil_str, shots)

        mock_translate.assert_called_once_with(
            native_quil=quil_str,
            num_shots=shots,
            quantum_processor_id=DEVICE_ID,
            client=rigetti_device.client,
            translation_options=None,
        )

    def test_submit_calls_qpu_submit_with_correct_args(self, rigetti_device: RigettiDevice) -> None:
        """_submit must pass the translated program and client to qpu_submit."""
        quil_str, shots = self._make_quil(shots=1)
        _, _, mock_submit = _mock_submit_pipeline(rigetti_device, quil_str, shots)

        # execution_options defaults to None when not passed at submit-time;
        # qcs_sdk falls back to the Gateway connection strategy.
        mock_submit.assert_called_once_with(
            program="TRANSLATED_BINARY",
            patch_values={},
            quantum_processor_id=DEVICE_ID,
            client=rigetti_device.client,
            execution_options=None,
        )

    def test_submit_forwards_execution_options_to_qpu_submit(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A custom execution_options kwarg on submit() must reach qpu_submit."""
        quil_str, shots = self._make_quil(shots=1)
        custom_opts = MagicMock(name="ExecutionOptions")

        _, _, mock_submit = _mock_submit_pipeline(
            rigetti_device, quil_str, shots, execution_options=custom_opts
        )

        assert mock_submit.call_args.kwargs["execution_options"] is custom_opts

    def test_submit_stores_execution_options_on_returned_job(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """The RigettiJob returned by submit() must carry the execution_options."""
        quil_str, shots = self._make_quil(shots=1)
        custom_opts = MagicMock(name="ExecutionOptions")

        job, _, _ = _mock_submit_pipeline(
            rigetti_device, quil_str, shots, execution_options=custom_opts
        )

        assert job._execution_options is custom_opts

    def test_submit_raises_rigetti_job_error_on_submission_error(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A SubmissionError from qpu_submit must be wrapped in RigettiJobError."""
        quil_str, shots = self._make_quil(shots=1)

        fake_translation_result = MagicMock()
        fake_translation_result.program = "TRANSLATED"
        fake_translation_result.ro_sources = {"ro[0]": "q0"}

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

    def test_submit_translation_failure_raises_job_error(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A translation failure must be wrapped in RigettiJobError."""
        quil_str, shots = self._make_quil(shots=1)

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                side_effect=RuntimeError("translation error"),
            ),
            pytest.raises(RigettiJobError, match="Translation failed"),
        ):
            rigetti_device.submit(quil_str, shots=shots)

    def test_submit_job_stores_correct_num_shots(self, rigetti_device: RigettiDevice) -> None:
        """The returned RigettiJob must store the same num_shots passed to submit."""
        shots = 7
        quil_str, _ = self._make_quil(shots=shots)
        job, _, _ = _mock_submit_pipeline(rigetti_device, quil_str, shots)

        assert job._num_shots == shots

    def test_submit_requires_shots(self, rigetti_device: RigettiDevice) -> None:
        """submit() declares shots as a required positional/keyword argument."""
        quil_str, _ = self._make_quil()

        # Omitting shots is a Python-level signature violation.
        with pytest.raises(TypeError, match="shots"):
            rigetti_device.submit(quil_str)  # pylint: disable=missing-kwoa

    def test_submit_raises_rigetti_job_error_when_shots_not_positive(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """_submit must raise RigettiJobError when shots <= 0."""
        quil_str, _ = self._make_quil()

        with pytest.raises(RigettiJobError, match="Shots"):
            rigetti_device.submit(quil_str, shots=0)

    def test_submit_passes_ro_sources_to_job(self, rigetti_device: RigettiDevice) -> None:
        """The RigettiJob returned by _submit must carry translation_result.ro_sources."""
        quil_str, shots = self._make_quil(shots=2)
        ro_sources = {"ro[0]": "q0_readout", "ro[1]": "q1_readout"}
        job, _, _ = _mock_submit_pipeline(rigetti_device, quil_str, shots, ro_sources=ro_sources)

        assert job._ro_sources == ro_sources

    def test_submit_list_returns_list_of_jobs(self, rigetti_device: RigettiDevice) -> None:
        """Submitting a list of Quil strings must return a list of RigettiJobs."""
        quil_strings = [self._make_quil(shots=3)[0], self._make_quil(shots=3)[0]]

        fake_translation_result = MagicMock()
        fake_translation_result.program = "TRANSLATED"
        fake_translation_result.ro_sources = {"ro[0]": "q0"}

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
        quil_strings = [
            self._make_quil(shots=3, qubit=0)[0],
            self._make_quil(shots=3, qubit=1)[0],
        ]

        fake_translation_result = MagicMock()
        fake_translation_result.program = "TRANSLATED"
        fake_translation_result.ro_sources = {"ro[0]": "q0"}

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


# ===========================================================================
# Device – repr / str
# ===========================================================================


def test_rigetti_device_str_repr(rigetti_device: RigettiDevice) -> None:
    """str/repr of RigettiDevice must mention the class name and device ID."""
    text = str(rigetti_device)
    assert "RigettiDevice" in text
    assert DEVICE_ID in text


def test_rigetti_device_str_format(rigetti_device: RigettiDevice) -> None:
    """__str__ must follow the SDK convention: ClassName('device_id')."""
    assert str(rigetti_device) == f"RigettiDevice('{DEVICE_ID}')"


# ===========================================================================
# Device – _parse_runtime_options
# ===========================================================================


class TestParseRuntimeOptions:
    """Tests for RigettiDevice._parse_runtime_options."""

    def test_none_returns_none(self) -> None:
        """None input returns None."""
        assert RigettiDevice._parse_runtime_options(None) is None

    def test_empty_dict_returns_none(self) -> None:
        """Empty dict returns None."""
        assert RigettiDevice._parse_runtime_options({}) is None

    def test_translation_keys_build_translation_opts(self) -> None:
        """Translation keys produce a TranslationOptions instance."""
        result = RigettiDevice._parse_runtime_options(
            {"prepend_default_calibrations": False, "passive_reset_delay_seconds": 100e-6}
        )
        assert isinstance(result, TranslationOptions)

    def test_unknown_keys_are_silently_ignored(self) -> None:
        """Unrecognized keys do not cause errors."""
        result = RigettiDevice._parse_runtime_options(
            {"unknown_key": "some_value", "another_key": 42}
        )
        assert result is None


# ===========================================================================
# Device – transform with compiler options
# ===========================================================================


class TestRigettiDeviceTransformWithCompilerOptions:
    """Tests for transient _compiler_options flowing into compile_program."""

    def test_transform_passes_compiler_options_to_compile_program(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """When _compiler_options is set, compile_program must receive options=."""
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))

        opts = CompilerOpts(timeout=60.0)
        rigetti_device._compiler_options = opts
        fake_comp = _mock_compile_pipeline()

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.TargetDevice.from_isa",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ) as mock_compile,
        ):
            rigetti_device.transform(program)

        assert mock_compile.call_args.kwargs["options"] is opts

    def test_transform_defaults_to_none_options(self, rigetti_device: RigettiDevice) -> None:
        """Without _compiler_options set, compile_program receives options=None."""
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))
        fake_comp = _mock_compile_pipeline()

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.TargetDevice.from_isa",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ) as mock_compile,
        ):
            rigetti_device.transform(program)

        assert mock_compile.call_args.kwargs["options"] is None


# ===========================================================================
# Device – submit with runtime_options
# ===========================================================================


class TestRigettiDeviceSubmitRuntimeOptions:
    """Tests for runtime_options being parsed into TranslationOptions in submit()."""

    def _make_quil(self) -> str:
        """Build a minimal Quil string for submission tests."""
        p = pyquil.Program()
        p.inst(pyquil.gates.RZ(0.5, 0))
        p.inst(pyquil.gates.MEASURE(0, None))
        return p.out()

    def test_submit_parses_runtime_options_to_translation_options(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """runtime_options translation keys must reach translate() as TranslationOptions."""
        quil_str = self._make_quil()

        fake_translation_result = MagicMock()
        fake_translation_result.program = "TRANSLATED"
        fake_translation_result.ro_sources = {"ro[0]": "q0"}

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
            rigetti_device.submit(
                quil_str,
                shots=1,
                runtime_options={"prepend_default_calibrations": False},
            )

        translation_opts = mock_translate.call_args.kwargs["translation_options"]
        assert isinstance(translation_opts, TranslationOptions)

    def test_submit_batch_parses_runtime_options_for_each_translate(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Each translate() call in a batch gets TranslationOptions parsed from runtime_options."""
        quil_strings = [self._make_quil(), self._make_quil()]

        fake_translation_result = MagicMock()
        fake_translation_result.program = "TRANSLATED"
        fake_translation_result.ro_sources = {"ro[0]": "q0"}

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
            rigetti_device.submit(
                quil_strings,
                shots=1,
                runtime_options={"prepend_default_calibrations": False},
            )

        assert mock_translate.call_count == 2
        for call in mock_translate.call_args_list:
            assert isinstance(call.kwargs["translation_options"], TranslationOptions)

    def test_submit_none_runtime_options_passes_none_translation(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """submit() with no runtime_options passes translation_options=None to translate()."""
        quil_str = self._make_quil()

        fake_translation_result = MagicMock()
        fake_translation_result.program = "TRANSLATED"
        fake_translation_result.ro_sources = {"ro[0]": "q0"}

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
            rigetti_device.submit(quil_str, shots=1)

        assert mock_translate.call_args.kwargs["translation_options"] is None


# ===========================================================================
# Device – run with runtime_options
# ===========================================================================


class TestRigettiDeviceRunRuntimeOptions:
    """Tests for runtime_options flowing from the base class run() to submit()."""

    def test_run_forwards_translation_opts_to_translate(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """runtime_options translation keys must reach translate() via base run() -> submit()."""
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))
        fake_comp = _mock_compile_pipeline()

        fake_translation_result = MagicMock()
        fake_translation_result.program = "TRANSLATED"
        fake_translation_result.ro_sources = {"ro[0]": "q0"}

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.list_quantum_processors",
                return_value=[DEVICE_ID],
            ),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.TargetDevice.from_isa",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ),
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ) as mock_translate,
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ),
        ):
            rigetti_device.run(
                program,
                shots=1,
                runtime_options={"prepend_default_calibrations": False},
            )

        translation_opts_passed = mock_translate.call_args.kwargs["translation_options"]
        assert isinstance(translation_opts_passed, TranslationOptions)

    def test_run_no_options_backward_compat(self, rigetti_device: RigettiDevice) -> None:
        """run() with no runtime_options must pass translation_options=None to translate()."""
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))
        fake_comp = _mock_compile_pipeline()

        fake_translation_result = MagicMock()
        fake_translation_result.program = "TRANSLATED"
        fake_translation_result.ro_sources = {"ro[0]": "q0"}

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.list_quantum_processors",
                return_value=[DEVICE_ID],
            ),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.TargetDevice.from_isa",
                return_value=MagicMock(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ),
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ) as mock_translate,
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ),
        ):
            job = rigetti_device.run(program, shots=1)

        assert isinstance(job, RigettiJob)
        assert mock_translate.call_args.kwargs["translation_options"] is None

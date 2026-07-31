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
import json
import logging
import re
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
    from qcs_sdk.compiler.quilc import DEFAULT_COMPILER_TIMEOUT, CompilerOpts
    from qcs_sdk.qpu import ListQuantumProcessorsError
    from qcs_sdk.qpu.api import SubmissionError
    from qcs_sdk.qpu.isa import InstructionSetArchitecture
    from qcs_sdk.qpu.translation import TranslationOptions

    from qbraid.runtime.rigetti import RigettiDevice, RigettiJob
    from qbraid.runtime.rigetti.device import (
        DEFAULT_COMPILER_TIMEOUT_S,
        RigettiDeviceError,
        non_native_gate_counts,
        quil_t_instruction_counts,
    )
    from qbraid.runtime.rigetti.job import RigettiJobError
    from qbraid.transpiler import transpile
else:
    RigettiDevice = None
    RigettiJob = None
    # Referenced at module import time by a parametrize list below, which is evaluated
    # even though pytestmark skips every test in the file.
    DEFAULT_COMPILER_TIMEOUT_S = None


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


# Trimmed from the live Cepheus-1-108Q ISA returned by QCS
# `get_instruction_set_architecture` on 2026-07-29: nodes 0-2 are kept, and the
# operation set, node counts, parameters, and characteristics are verbatim. Note that
# the real native set is only I / RX / RZ / CZ / MEASURE -- no H, no CNOT, and no XY or
# ISWAP either, which several Rigetti generations do have.
CEPHEUS_ISA_NODES = (0, 1, 2)
NATIVE_INSTRUCTION_NAMES = ("I", "RX", "RZ", "MEASURE", "CZ")
CEPHEUS_ISA_PAYLOAD = {
    "name": "Cepheus-1-108Q",
    "architecture": {
        "family": "Ankaa",
        "nodes": [{"node_id": node} for node in CEPHEUS_ISA_NODES],
        "edges": [{"node_ids": [0, 1]}, {"node_ids": [1, 2]}],
    },
    # quilc's TargetDevice.from_isa rejects an ISA without these two, so they are part
    # of what "a real ISA" means here, not decoration.
    "benchmarks": [
        {
            "characteristics": [],
            "name": "randomized_benchmark_1q",
            "node_count": 1,
            "parameters": [],
            "sites": [
                {
                    "characteristics": [
                        {
                            "error": 2.1909572855690584e-05,
                            "name": "fRB",
                            "parameter_values": [],
                            "timestamp": "2026-07-29T14:20:53+00:00",
                            "value": 0.9990428041297528,
                        }
                    ],
                    "node_ids": [n],
                }
                for n in CEPHEUS_ISA_NODES
            ],
        },
        {
            "characteristics": [],
            "name": "randomized_benchmark_simultaneous_1q",
            "node_count": len(CEPHEUS_ISA_NODES),
            "parameters": [],
            "sites": [
                {
                    "characteristics": [
                        {
                            "error": 0.00013824098221960836,
                            "name": "fRB",
                            "node_ids": [n],
                            "parameter_values": [],
                            "timestamp": "2026-07-29T14:26:24+00:00",
                            "value": 0.9973012078343386,
                        }
                        for n in CEPHEUS_ISA_NODES
                    ],
                    "node_ids": list(CEPHEUS_ISA_NODES),
                }
            ],
        },
    ],
    "instructions": [
        {
            "characteristics": [],
            "name": "I",
            "node_count": 1,
            "parameters": [],
            "sites": [{"characteristics": [], "node_ids": [n]} for n in CEPHEUS_ISA_NODES],
        },
        {
            "characteristics": [],
            "name": "RX",
            "node_count": 1,
            "parameters": [{"name": "theta"}],
            "sites": [{"characteristics": [], "node_ids": [n]} for n in CEPHEUS_ISA_NODES],
        },
        {
            "characteristics": [],
            "name": "RZ",
            "node_count": 1,
            "parameters": [{"name": "theta"}],
            "sites": [{"characteristics": [], "node_ids": [n]} for n in CEPHEUS_ISA_NODES],
        },
        {
            "characteristics": [],
            "name": "MEASURE",
            "node_count": 1,
            "parameters": [],
            "sites": [
                {
                    "characteristics": [
                        {
                            "name": "fRO",
                            "parameter_values": [],
                            "timestamp": "2026-07-29T16:01:02+00:00",
                            "value": 0.957,
                        }
                    ],
                    "node_ids": [n],
                }
                for n in CEPHEUS_ISA_NODES
            ],
        },
        {
            "characteristics": [],
            "name": "CZ",
            "node_count": 2,
            "parameters": [],
            "sites": [
                {
                    "characteristics": [
                        {
                            "error": 0.0017594379667536008,
                            "name": "fCZ",
                            "parameter_values": [],
                            "timestamp": "2026-07-29T15:04:14+00:00",
                            "value": 0.9928065122135934,
                        }
                    ],
                    "node_ids": edge,
                }
                for edge in ([0, 1], [1, 2])
            ],
        },
    ],
}


def _cepheus_isa() -> InstructionSetArchitecture:
    """Return the trimmed production ISA, validated by qcs_sdk's own parser.

    Going through `InstructionSetArchitecture.from_raw` rather than hand-building a
    MagicMock means the fixture is checked against the vendor schema on every run: if
    qcs_sdk changes the ISA shape, this fails naming the field instead of quietly
    testing against a shape QCS never returns.
    """
    return InstructionSetArchitecture.from_raw(json.dumps(CEPHEUS_ISA_PAYLOAD))


# Verbatim from a production job's statusMsg, minus the wrapper this device adds. This
# is what `compile_program` raises when the client-side deadline expires: lisp-flavoured
# and silent about the knob that controls it.
QUILC_TIMEOUT_ERROR = (
    "Problem compiling quil program: compilation error from RPCQ: Received error "
    "message from server: Execution timed out.  Note: time limit: 30.0d0 seconds."
)

# The shape of the program that produced the production failure above: an OpenQASM 3
# circuit built from a custom `rzx` gate, with a single trailing barrier before the
# measurements. Reduced from 19 qubits to 3; the barrier, the gate body, and the
# resulting "H 1" at instruction 0 are unchanged.
RZX_QASM3 = """OPENQASM 3.0;
include "stdgates.inc";
gate rzx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
}
bit[3] meas;
qubit[3] q;
rzx(0) q[0], q[1];
rzx(0) q[1], q[2];
barrier q[0], q[1], q[2];
meas[0] = measure q[0];
meas[1] = measure q[1];
meas[2] = measure q[2];
"""


def _rzx_program() -> pyquil.Program:
    """Lower `RZX_QASM3` to pyquil the way `run()` does, via the conversion graph.

    Using the real transpiler rather than a hand-typed Quil string keeps the FENCE
    under test the one `openqasm3_to_pyquil` actually emits for a `barrier`.
    """
    return transpile(RZX_QASM3, "pyquil")


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
        """A compilation failure must be wrapped in RigettiDeviceError, and must surface
        quilc's own reason -- that is the only thing that says *why* it failed."""
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
            pytest.raises(RigettiDeviceError, match="quilc failed to compile") as exc_info,
        ):
            rigetti_device.transform(program)

        # The underlying cause must be in the message, not only the __cause__ chain:
        # the job document persists str(exc), so a generic message strands the reason.
        assert "ISA unavailable" in str(exc_info.value)

    @pytest.mark.parametrize(
        "quil_t_line",
        [
            "DELAY 0 0.0005",
            'DELAY 0 "rf" 1e-6',
            "FENCE 0",
            'SHIFT-PHASE 0 "rf" 1.0',
        ],
        ids=["delay_qubit", "delay_frame", "fence", "shift_phase"],
    )
    def test_transform_bypasses_quilc_for_quil_t(
        self, rigetti_device: RigettiDevice, quil_t_line: str
    ) -> None:
        """quilc cannot compile Quil-T, so such programs must skip it untouched.

        Sending them to quilc is what produced the opaque
        "5.0d-4 is not of type QUBIT" failure from the RPCQ server. This holds only
        while the remaining gates are already native, which they are here (RX).
        """
        # pylint: disable-next=import-outside-toplevel
        import pyquil

        program = pyquil.Program(f"DECLARE ro BIT[1]\nRX(pi) 0\n{quil_t_line}\nMEASURE 0 ro[0]")

        with (
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            patch("qbraid.runtime.rigetti.device.compile_program") as mock_compile,
            patch.object(rigetti_device, "_probe_quilc_reachable") as mock_probe,
        ):
            result = rigetti_device.transform(program)

        mock_compile.assert_not_called()
        mock_probe.assert_not_called()
        assert result.out() == program.out()

    def test_transform_bypasses_quilc_when_isa_unavailable(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A failed ISA lookup must not break the bypass; nativity is only diagnostic."""
        # pylint: disable-next=import-outside-toplevel
        import pyquil

        program = pyquil.Program("DECLARE ro BIT[1]\nH 0\nDELAY 0 0.0005\nMEASURE 0 ro[0]")

        with (
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                side_effect=RuntimeError("ISA unavailable"),
            ),
            patch("qbraid.runtime.rigetti.device.compile_program") as mock_compile,
        ):
            result = rigetti_device.transform(program)

        mock_compile.assert_not_called()
        assert result.out() == program.out()

    def test_transform_still_uses_quilc_without_quil_t(self, rigetti_device: RigettiDevice) -> None:
        """A plain gate-model program must still be compiled by quilc as before."""
        # pylint: disable=import-outside-toplevel
        import pyquil
        import pyquil.gates

        # pylint: enable=import-outside-toplevel
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch("qbraid.runtime.rigetti.device.get_instruction_set_architecture"),
            patch("qbraid.runtime.rigetti.device.TargetDevice"),
            patch("qbraid.runtime.rigetti.device.compile_program") as mock_compile,
        ):
            mock_compile.return_value.program.to_quil.return_value = "RX(pi/2) 0\n"
            rigetti_device.transform(program)

        mock_compile.assert_called_once()

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

    def test_submit_translation_failure_surfaces_underlying_reason(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """The translation service's own reason must reach the user.

        Not every translation failure is a gate-nativity problem, so the message
        must carry the real cause rather than a fixed hint.
        """
        quil_str, shots = self._make_quil(shots=1)
        reason = 'at instruction 0 ("H 0"): this instruction must be replaced or decomposed'

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                side_effect=RuntimeError(reason),
            ),
            pytest.raises(RigettiJobError, match=re.escape(reason)) as exc_info,
        ):
            rigetti_device.submit(quil_str, shots=shots)

        assert isinstance(exc_info.value.__cause__, RuntimeError)

    def test_submit_translation_failure_reports_non_nativity_causes(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A non-gate-related failure must not be described as a gate problem."""
        quil_str, shots = self._make_quil(shots=1)

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                side_effect=RuntimeError("input program error: program has no defined frames"),
            ),
            pytest.raises(RigettiJobError, match="program has no defined frames") as exc_info,
        ):
            rigetti_device.submit(quil_str, shots=shots)

        assert "only native gates" not in str(exc_info.value)

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

    def test_unknown_keys_are_ignored_but_warned_about(self, caplog) -> None:
        """Unrecognized keys do not cause errors, but must not pass in silence.

        Silently dropping them is indistinguishable from applying them: a user passing
        `compiler_timeout` before it was supported got no signal that it did nothing.
        """
        with caplog.at_level(logging.WARNING, logger="qbraid"):
            result = RigettiDevice._parse_runtime_options(
                {"unknown_key": "some_value", "another_key": 42}
            )

        assert result is None
        assert "unknown_key" in caplog.text
        assert "another_key" in caplog.text

    def test_known_keys_do_not_warn(self, caplog) -> None:
        """Recognized translation and compiler keys must not be reported as ignored."""
        with caplog.at_level(logging.WARNING, logger="qbraid"):
            RigettiDevice._parse_runtime_options(
                {"prepend_default_calibrations": False, "compiler_timeout": 300}
            )

        assert "Ignoring unrecognized" not in caplog.text


# ===========================================================================
# Device – _parse_compiler_options
# ===========================================================================


class TestParseCompilerOptions:
    """Tests for RigettiDevice._parse_compiler_options and _compiler_timeout."""

    def test_none_and_empty_return_none(self) -> None:
        """Without compiler keys there is nothing to build; transform applies the default."""
        assert RigettiDevice._parse_compiler_options(None) is None
        assert RigettiDevice._parse_compiler_options({}) is None

    def test_translation_only_keys_return_none(self) -> None:
        """Translation keys are not compiler keys."""
        assert (
            RigettiDevice._parse_compiler_options({"prepend_default_calibrations": False}) is None
        )

    def test_compiler_timeout_builds_opts(self) -> None:
        """compiler_timeout must reach CompilerOpts.timeout."""
        with patch("qbraid.runtime.rigetti.device.CompilerOpts") as mock_opts:
            RigettiDevice._parse_compiler_options({"compiler_timeout": 300})

        assert mock_opts.call_args.kwargs == {"timeout": 300}

    def test_protoquil_alone_keeps_default_timeout(self) -> None:
        """protoquil on its own must not silently revert the timeout to qcs_sdk's 30s."""
        with patch("qbraid.runtime.rigetti.device.CompilerOpts") as mock_opts:
            RigettiDevice._parse_compiler_options({"protoquil": True})

        assert mock_opts.call_args.kwargs == {
            "timeout": DEFAULT_COMPILER_TIMEOUT_S,
            "protoquil": True,
        }

    def test_explicit_none_timeout_is_honored(self) -> None:
        """compiler_timeout=None means "no limit" and must not be replaced by the default."""
        with patch("qbraid.runtime.rigetti.device.CompilerOpts") as mock_opts:
            RigettiDevice._parse_compiler_options({"compiler_timeout": None})

        assert mock_opts.call_args.kwargs == {"timeout": None}

    def test_returns_compiler_opts_instance(self) -> None:
        """The unpatched path returns a real CompilerOpts."""
        assert isinstance(
            RigettiDevice._parse_compiler_options({"compiler_timeout": 300}), CompilerOpts
        )

    @pytest.mark.parametrize(
        "runtime_options,expected",
        [
            (None, DEFAULT_COMPILER_TIMEOUT_S),
            ({}, DEFAULT_COMPILER_TIMEOUT_S),
            ({"protoquil": True}, DEFAULT_COMPILER_TIMEOUT_S),
            ({"compiler_timeout": 300}, 300),
            ({"compiler_timeout": None}, None),
        ],
        ids=["none", "empty", "protoquil_only", "explicit", "unlimited"],
    )
    def test_compiler_timeout_resolution(self, runtime_options, expected) -> None:
        """The timeout reported in error messages must match what quilc was given."""
        assert RigettiDevice._compiler_timeout(runtime_options) == expected

    def test_default_timeout_is_longer_than_qcs_sdk_default(self) -> None:
        """The whole point of the default: qcs_sdk's 30s cuts off ordinary compilations."""
        assert DEFAULT_COMPILER_TIMEOUT_S == 180.0
        assert DEFAULT_COMPILER_TIMEOUT_S > DEFAULT_COMPILER_TIMEOUT


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

    def test_transform_defaults_to_configured_timeout(self, rigetti_device: RigettiDevice) -> None:
        """Without _compiler_options set, quilc must get our default timeout, not None.

        Passing options=None leaves qcs_sdk's 30s default in force, which is what cut
        off compilations that finish in 20-230s against a 100+ qubit ISA.
        """
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
            patch("qbraid.runtime.rigetti.device.CompilerOpts") as mock_opts,
        ):
            rigetti_device.transform(program)

        assert mock_opts.call_args.kwargs == {"timeout": DEFAULT_COMPILER_TIMEOUT_S}
        assert mock_compile.call_args.kwargs["options"] is mock_opts.return_value

    def test_transform_rewrites_quilc_timeout_error(self, rigetti_device: RigettiDevice) -> None:
        """A quilc timeout must name the knob that controls it, not just quote quilc."""
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))
        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                side_effect=RuntimeError(QUILC_TIMEOUT_ERROR),
            ),
            pytest.raises(RigettiDeviceError) as exc_info,
        ):
            rigetti_device.transform(program)

        message = str(exc_info.value)
        assert "compiler_timeout" in message
        assert f"within {DEFAULT_COMPILER_TIMEOUT_S}s" in message
        # quilc's own text is still carried, so nothing is lost by rewriting.
        assert "time limit: 30.0d0 seconds" in message

    def test_isa_lookup_timeout_is_not_reported_as_a_compiler_timeout(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """An ISA fetch is a network call and can say "timed out" itself.

        Matching the timeout markers against it would answer a QCS outage with advice
        about `compiler_timeout`, which is why the ISA lookup sits outside the block
        whose exceptions are inspected for those markers.
        """
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                side_effect=RuntimeError("error sending request: operation timed out"),
            ),
            pytest.raises(RigettiDeviceError, match="quilc failed to compile") as exc_info,
        ):
            rigetti_device.transform(program)

        assert "compiler_timeout" not in str(exc_info.value)
        assert "operation timed out" in str(exc_info.value)

    def test_transform_non_timeout_error_keeps_generic_wrapper(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Only timeouts are rewritten; other quilc failures keep the existing message."""
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                side_effect=RuntimeError("unsupported gate"),
            ),
            pytest.raises(RigettiDeviceError, match="quilc failed to compile") as exc_info,
        ):
            rigetti_device.transform(program)

        assert "compiler_timeout" not in str(exc_info.value)


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


# ===========================================================================
# Program inspection helpers
# ===========================================================================


class TestQuilTInstructionCounts:
    """Tests for quil_t_instruction_counts."""

    def test_gate_model_program_has_no_quil_t(self) -> None:
        """A pure gate-model program reports nothing."""
        program = pyquil.Program("DECLARE ro BIT[1]\nH 0\nMEASURE 0 ro[0]\n")
        assert not quil_t_instruction_counts(program)

    def test_fence_is_counted_by_name(self) -> None:
        """A barrier lowered to FENCE must be identifiable as *only* a fence."""
        program = pyquil.Program("DECLARE ro BIT[1]\nH 0\nFENCE 0\nFENCE\nMEASURE 0 ro[0]\n")
        assert quil_t_instruction_counts(program) == {"FENCE": 2}

    def test_mixed_quil_t_instructions_are_counted_separately(self) -> None:
        """DELAY and FENCE must not be conflated: only FENCE is safe to drop."""
        program = pyquil.Program("H 0\nFENCE 0\nDELAY 0 1e-6\nDELAY 1 1e-6\n")
        assert quil_t_instruction_counts(program) == {"FENCE": 1, "DELAY": 2}

    def test_definitions_are_counted(self) -> None:
        """DEFCAL / DEFFRAME make a program genuinely pulse-level."""
        program = pyquil.Program(
            'DEFFRAME 0 "rf":\n    SAMPLE-RATE: 1.0\n\nDEFCAL X 0:\n    NOP\n\nX 0\n'
        )
        assert quil_t_instruction_counts(program) == {"DEFFRAME": 1, "DEFCAL": 1}

    def test_agrees_with_contains_quil_t(self) -> None:
        """The counts helper and the existing boolean must never disagree."""
        # pylint: disable-next=import-outside-toplevel
        from qbraid.runtime.rigetti.device import contains_quil_t

        for quil in (
            "H 0\n",
            "H 0\nFENCE 0\n",
            "H 0\nDELAY 0 1e-6\n",
            'DEFFRAME 0 "rf":\n    SAMPLE-RATE: 1.0\n\nH 0\n',
        ):
            program = pyquil.Program(quil)
            assert bool(quil_t_instruction_counts(program)) == contains_quil_t(program)


class TestNonNativeGateCounts:
    """Tests for non_native_gate_counts."""

    NATIVE = set(NATIVE_INSTRUCTION_NAMES)

    def test_native_program_reports_nothing(self) -> None:
        """RX/RZ/CZ programs are exactly what the QCS translator accepts."""
        program = pyquil.Program("DECLARE ro BIT[1]\nRX(pi) 0\nCZ 0 1\nMEASURE 0 ro[0]\n")
        assert not non_native_gate_counts(program, self.NATIVE)

    def test_non_native_gates_are_counted(self) -> None:
        """H and CNOT are the gates qiskit-derived programs actually carry."""
        program = pyquil.Program("H 0\nH 1\nCNOT 0 1\nRZ(0.3) 0\n")
        assert non_native_gate_counts(program, self.NATIVE) == {"H": 2, "CNOT": 1}

    def test_modified_gates_are_non_native(self) -> None:
        """No Rigetti QPU executes a modifier directly, even on a native base gate."""
        program = pyquil.Program("CONTROLLED X 0 1\nDAGGER RX(pi/2) 0\n")
        assert non_native_gate_counts(program, self.NATIVE) == {
            "CONTROLLED X": 1,
            "DAGGER RX": 1,
        }

    def test_measure_and_declare_are_not_gates(self) -> None:
        """Non-gate instructions must never be reported as non-native gates."""
        program = pyquil.Program("DECLARE ro BIT[1]\nMEASURE 0 ro[0]\nRESET\n")
        assert not non_native_gate_counts(program, self.NATIVE)

    def test_parameterized_native_name_is_not_flagged(self) -> None:
        """The check is deliberately one-sided: RX(0.3) is not native, but is not flagged.

        Flagging it would need angle-range knowledge the ISA does not carry, and a
        false positive would turn a program that runs today into an error.
        """
        program = pyquil.Program("RX(0.3) 0\n")
        assert not non_native_gate_counts(program, self.NATIVE)


# ===========================================================================
# Device – transform: Quil-T and quilc interaction
# ===========================================================================


class TestTransformQuilTHandling:
    """Tests for how transform() reconciles Quil-T with quilc's native-gate requirement.

    A single FENCE used to disable gate compilation for the whole program: OpenQASM
    `barrier` lowers to FENCE, qiskit's measure_all() inserts a barrier, and the
    resulting program bypassed quilc and was rejected by QCS translation at the first
    non-native gate.
    """

    def test_openqasm_barrier_program_reaches_quilc(self, rigetti_device: RigettiDevice) -> None:
        """The test that would have caught the bug, driven from its real source.

        Production job `rigetti:rigetti:qpu:cepheus-1-108q-a9e9-qjob-6a65a76c0936bd6f4
        cecb68b` was an OpenQASM 3 circuit with one `barrier` before its measurements.
        The barrier became one FENCE, transform() saw Quil-T and skipped quilc, and QCS
        translation rejected the whole 1038-instruction program at its first gate:
        `at instruction 0 ("H 1"): this instruction must be replaced or decomposed
        prior to compilation, perhaps by `quilc``. Nothing in the user's source looked
        pulse-related.

        Written against the real transpiler rather than a hand-typed Quil string, so it
        keeps failing if `barrier` ever stops lowering to FENCE for some other reason.
        """
        program = _rzx_program()
        # The premise, asserted rather than assumed: a plain barrier really does produce
        # a FENCE, and the gates it disabled compilation for really are non-native.
        assert "FENCE" in program.out()
        assert quil_t_instruction_counts(program) == {"FENCE": 1}
        assert non_native_gate_counts(program, set(NATIVE_INSTRUCTION_NAMES)) == {"H": 4, "CNOT": 4}

        fake_comp = _mock_compile_pipeline(compiled_quil="RX(pi/2) 0\n")

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ) as mock_compile,
        ):
            rigetti_device.transform(program)

        mock_compile.assert_called_once()
        compiled_input = mock_compile.call_args.kwargs["quil"]
        # The fence is dropped before compiling: quilc rejects Quil-T outright, and a
        # source-position fence has no well-defined image in its rewritten output.
        assert "FENCE" not in compiled_input
        # Everything else survives, so quilc gets the program it can actually nativize.
        assert compiled_input.count("CNOT") == 4
        assert compiled_input.count("MEASURE") == 3

    def test_program_supplying_its_own_calibrations_still_bypasses(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Regression: a DEFCAL for a non-ISA gate means the program never needed quilc.

        `H` is not in the Cepheus ISA, so a name-based nativity check calls it
        non-native. But a program that ships `DEFCAL H 0` is exactly the pulse-level
        workflow the quilc bypass exists for: QCS translation runs the supplied
        calibration. An earlier revision of this check raised RigettiDeviceError here,
        breaking a program that ran fine before the fix.
        """
        program = pyquil.Program(
            "DECLARE ro BIT[1]\nDEFCAL H 0:\n    RX(pi/2) 0\n\nH 0\nMEASURE 0 ro[0]\n"
        )

        with (
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            patch("qbraid.runtime.rigetti.device.compile_program") as mock_compile,
        ):
            result = rigetti_device.transform(program)

        mock_compile.assert_not_called()
        assert result.out() == program.out()

    def test_uncalibrated_gate_alongside_a_calibrated_one_still_raises(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """The DEFCAL carve-out must not become a blanket exemption for the program."""
        program = pyquil.Program(
            "DECLARE ro BIT[2]\nDEFCAL H 0:\n    RX(pi/2) 0\n\nH 0\nCNOT 0 1\n"
        )

        with (
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            pytest.raises(RigettiDeviceError) as exc_info,
        ):
            rigetti_device.transform(program)

        message = str(exc_info.value)
        assert "CNOT (1)" in message
        # H is calibrated by the program, so blaming it would send the user in circles.
        assert "H (1)" not in message

    def test_fence_only_program_with_native_gates_still_bypasses(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Programs that run today must keep running today, byte for byte.

        An already-native program bypassing quilc keeps both its fences and its
        explicit qubit placement; sending it to quilc would rewire it.
        """
        program = pyquil.Program("DECLARE ro BIT[1]\nRX(pi) 0\nFENCE 0\nMEASURE 0 ro[0]\n")

        with (
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            patch("qbraid.runtime.rigetti.device.compile_program") as mock_compile,
        ):
            result = rigetti_device.transform(program)

        mock_compile.assert_not_called()
        assert result.out() == program.out()

    def test_other_quil_t_with_non_native_gates_raises(self, rigetti_device: RigettiDevice) -> None:
        """The residual case must fail fast here, not as opaque QCS translation text."""
        program = pyquil.Program("DECLARE ro BIT[2]\nH 0\nCNOT 0 1\nDELAY 0 1e-6\n")

        with (
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            patch("qbraid.runtime.rigetti.device.compile_program") as mock_compile,
            pytest.raises(RigettiDeviceError) as exc_info,
        ):
            rigetti_device.transform(program)

        mock_compile.assert_not_called()
        message = str(exc_info.value)
        assert DEVICE_ID in message
        assert "DELAY (1)" in message
        assert "H (1)" in message and "CNOT (1)" in message
        assert "2 non-native gate(s)" in message

    def test_error_mentions_barrier_when_a_fence_is_involved(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Without this note a user cannot connect "Quil-T" to anything they wrote."""
        program = pyquil.Program("DECLARE ro BIT[2]\nH 0\nFENCE 0 1\nDELAY 0 1e-6\n")

        with (
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            pytest.raises(RigettiDeviceError) as exc_info,
        ):
            rigetti_device.transform(program)

        message = str(exc_info.value)
        assert "barrier" in message
        assert "measure_all()" in message

    def test_error_omits_barrier_note_without_a_fence(self, rigetti_device: RigettiDevice) -> None:
        """A pure DELAY program has no barrier to blame; the note would be noise."""
        program = pyquil.Program("DECLARE ro BIT[1]\nH 0\nDELAY 0 1e-6\n")

        with (
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            pytest.raises(RigettiDeviceError) as exc_info,
        ):
            rigetti_device.transform(program)

        assert "measure_all()" not in str(exc_info.value)

    def test_fence_only_program_without_isa_falls_back_to_bypass(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A diagnostic ISA lookup failure must not change which path is taken."""
        program = _rzx_program()

        with (
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                side_effect=RuntimeError("ISA unavailable"),
            ),
            patch("qbraid.runtime.rigetti.device.compile_program") as mock_compile,
        ):
            result = rigetti_device.transform(program)

        mock_compile.assert_not_called()
        assert result.out() == program.out()


# ===========================================================================
# Device – run: compiler options wiring
# ===========================================================================


class TestRigettiDeviceRunCompilerOptions:
    """Tests for runtime_options quilc keys reaching transform() via run().

    run() compiles before it submits, so these cannot ride along with the translation
    options through submit(); they are published on a ContextVar for the call.
    """

    @staticmethod
    def _patched_run(rigetti_device: RigettiDevice, *run_args, run_input=None, **run_kwargs):
        """Run a program with the whole submit pipeline mocked out.

        `run_args` / `run_kwargs` are forwarded to `run()` verbatim, so a test can
        exercise the positional call shape as well as the keyword one.
        """
        program = run_input if run_input is not None else pyquil.Program(pyquil.gates.H(0))
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
                return_value=_cepheus_isa(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ) as mock_compile,
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ) as mock_translate,
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ),
            patch("qbraid.runtime.rigetti.device.CompilerOpts") as mock_opts,
        ):
            job = rigetti_device.run(program, *run_args, **run_kwargs)

        return job, mock_compile, mock_translate, mock_opts

    def test_compiler_timeout_reaches_quilc(self, rigetti_device: RigettiDevice) -> None:
        """The reported bug: compiler_timeout was accepted and then dropped entirely."""
        _, mock_compile, _, mock_opts = self._patched_run(
            rigetti_device, shots=1, runtime_options={"compiler_timeout": 300}
        )

        assert mock_opts.call_args.kwargs == {"timeout": 300}
        assert mock_compile.call_args.kwargs["options"] is mock_opts.return_value

    def test_positional_runtime_options_reach_quilc(self, rigetti_device: RigettiDevice) -> None:
        """`submit()` takes runtime_options positionally, so `run()` must accept it that way.

        Reading only `**kwargs` would drop `device.run(program, 1, None, {...})` in
        silence -- the same failure mode as the `compiler_timeout` bug this fixes.
        """
        _, mock_compile, _, mock_opts = self._patched_run(
            rigetti_device, 1, None, {"compiler_timeout": 300}
        )

        assert mock_opts.call_args.kwargs == {"timeout": 300}
        assert mock_compile.call_args.kwargs["options"] is mock_opts.return_value

    def test_unbindable_call_leaves_the_error_to_submit(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """Recovering runtime_options is a diagnostic and must never be what fails.

        When the call cannot be bound to submit()'s signature, submit() itself should
        report the mismatch; the lookup falls back to whatever `kwargs` holds.
        """
        options = {"compiler_timeout": 300}

        # Too many positionals for submit(): nothing to recover, and no exception.
        assert (
            rigetti_device._runtime_options_from_call(
                "PROGRAM", (1, None, options, "unexpected"), {}
            )
            is None
        )
        # Given both positionally and by keyword: still unbindable, keyword wins.
        assert (
            rigetti_device._runtime_options_from_call(
                "PROGRAM", (1, None, None), {"runtime_options": options}
            )
            is options
        )

    def test_compiler_and_translation_keys_coexist(self, rigetti_device: RigettiDevice) -> None:
        """One dict feeds two different stages; neither may swallow the other's keys."""
        _, mock_compile, mock_translate, mock_opts = self._patched_run(
            rigetti_device,
            shots=1,
            runtime_options={"compiler_timeout": 300, "prepend_default_calibrations": False},
        )

        assert mock_compile.call_args.kwargs["options"] is mock_opts.return_value
        assert isinstance(
            mock_translate.call_args.kwargs["translation_options"], TranslationOptions
        )

    def test_run_without_options_uses_default_timeout(self, rigetti_device: RigettiDevice) -> None:
        """No runtime_options still means our default, not qcs_sdk's 30s."""
        _, mock_compile, _, mock_opts = self._patched_run(rigetti_device, shots=1)

        assert mock_opts.call_args.kwargs == {"timeout": DEFAULT_COMPILER_TIMEOUT_S}
        assert mock_compile.call_args.kwargs["options"] is mock_opts.return_value

    def test_batch_run_applies_the_options_to_every_program(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """`run()` accepts a list, and transform() runs once per program.

        All of them are compiled inside the one `run()` call that set the ContextVar,
        so a batch must not get the default timeout for its second program onwards.
        """
        batch = [_rzx_program(), pyquil.Program(pyquil.gates.H(0))]

        _, mock_compile, mock_translate, mock_opts = self._patched_run(
            rigetti_device, run_input=batch, shots=1, runtime_options={"compiler_timeout": 300}
        )

        assert mock_compile.call_count == len(batch)
        assert all(
            call.kwargs["options"] is mock_opts.return_value for call in mock_compile.call_args_list
        )
        # Parsed once per run(), not once per program.
        assert [call.kwargs for call in mock_opts.call_args_list] == [{"timeout": 300}]
        assert mock_translate.call_count == len(batch)

    def test_transform_outside_run_uses_the_default(self, rigetti_device: RigettiDevice) -> None:
        """A caller reaching for transform()/submit() directly gets the default, not None.

        The ContextVar is only set by `run()`. Everything else must still land on
        DEFAULT_COMPILER_TIMEOUT_S rather than falling back to qcs_sdk's 30s.
        """
        program = pyquil.Program(pyquil.gates.H(0))

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=_mock_compile_pipeline(),
            ) as mock_compile,
            patch("qbraid.runtime.rigetti.device.CompilerOpts") as mock_opts,
        ):
            rigetti_device.transform(program)

        assert mock_opts.call_args.kwargs == {"timeout": DEFAULT_COMPILER_TIMEOUT_S}
        assert mock_compile.call_args.kwargs["options"] is mock_opts.return_value

    def test_direct_submit_warns_that_quilc_keys_do_nothing(
        self, rigetti_device: RigettiDevice, caplog
    ) -> None:
        """submit() never compiles, so its caller must be told the quilc keys are inert.

        This is the same silent drop as the original bug, one layer down: the key is
        recognized, so the unknown-key warning stays quiet, and nothing else would fire.
        """
        fake_translation_result = MagicMock()
        fake_translation_result.program = "TRANSLATED"
        fake_translation_result.ro_sources = {"ro[0]": "q0"}

        with (
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ),
            patch("qbraid.runtime.rigetti.device.qpu_submit", return_value=DUMMY_JOB_ID),
            caplog.at_level(logging.WARNING, logger="qbraid"),
        ):
            rigetti_device.submit("H 0\n", shots=1, runtime_options={"compiler_timeout": 300})

        assert "compiler_timeout" in caplog.text
        assert "run()" in caplog.text

    def test_run_does_not_warn_about_its_own_quilc_keys(
        self, rigetti_device: RigettiDevice, caplog
    ) -> None:
        """run() reaches submit() with the same dict, and must not warn about itself."""
        with caplog.at_level(logging.WARNING, logger="qbraid"):
            self._patched_run(rigetti_device, shots=1, runtime_options={"compiler_timeout": 300})

        assert "Pass them to run()" not in caplog.text

    def test_context_is_cleared_after_run(self, rigetti_device: RigettiDevice) -> None:
        """Per-run options must not leak into a later transform() on the same device."""
        # pylint: disable-next=import-outside-toplevel
        from qbraid.runtime.rigetti.device import _COMPILER_OPTIONS

        self._patched_run(rigetti_device, shots=1, runtime_options={"compiler_timeout": 300})

        assert _COMPILER_OPTIONS.get() is None

    def test_context_is_cleared_when_run_raises(self, rigetti_device: RigettiDevice) -> None:
        """A failed run must not strand its options in the context either."""
        # pylint: disable-next=import-outside-toplevel
        from qbraid.runtime.rigetti.device import _COMPILER_OPTIONS

        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                side_effect=RuntimeError("boom"),
            ),
            pytest.raises(RigettiDeviceError),
        ):
            rigetti_device.run(program, shots=1, runtime_options={"compiler_timeout": 300})

        assert _COMPILER_OPTIONS.get() is None

    def test_run_options_take_precedence_over_device_attribute(
        self, rigetti_device: RigettiDevice
    ) -> None:
        """A per-run timeout must win over one parked on the device."""
        rigetti_device._compiler_options = CompilerOpts(timeout=60.0)

        _, mock_compile, _, mock_opts = self._patched_run(
            rigetti_device, shots=1, runtime_options={"compiler_timeout": 300}
        )

        assert mock_compile.call_args.kwargs["options"] is mock_opts.return_value

    def test_timeout_error_reports_the_requested_limit(self, rigetti_device: RigettiDevice) -> None:
        """The rewritten timeout error must name the limit actually in force."""
        program = pyquil.Program()
        program.inst(pyquil.gates.H(0))

        with (
            patch.object(rigetti_device, "_probe_quilc_reachable"),
            patch(
                "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
                return_value=_cepheus_isa(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                side_effect=RuntimeError("exceeded time limit: 300.0d0 seconds"),
            ),
            pytest.raises(RigettiDeviceError, match="within 300s"),
        ):
            rigetti_device.run(program, shots=1, runtime_options={"compiler_timeout": 300})


# ===========================================================================
# Device – run: accepted input types
# ===========================================================================


class TestRigettiDeviceRunInputTypes:
    """run() sits before transpilation, so it accepts more than pyquil.Program.

    Only :meth:`transform` receives a `pyquil.Program`, because it runs after
    `apply_runtime_profile` has transpiled to the device's ProgramSpec type. The
    dominant real input is a raw OpenQASM string: qbraid-runtime-api hands
    `program.data` straight to `run()` for qasm2/qasm3 jobs.
    """

    QASM2 = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;
"""

    def test_run_accepts_a_raw_qasm_string(self, rigetti_device: RigettiDevice) -> None:
        """A str must be transpiled to pyquil and compiled, not rejected."""
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
                return_value=_cepheus_isa(),
            ),
            patch(
                "qbraid.runtime.rigetti.device.compile_program",
                return_value=fake_comp,
            ) as mock_compile,
            patch(
                "qbraid.runtime.rigetti.device.translate",
                return_value=fake_translation_result,
            ),
            patch(
                "qbraid.runtime.rigetti.device.qpu_submit",
                return_value=DUMMY_JOB_ID,
            ),
        ):
            job = rigetti_device.run(self.QASM2, shots=1)

        assert isinstance(job, RigettiJob)
        # transform() still saw a Program: transpilation happened in between.
        mock_compile.assert_called_once()
        assert isinstance(mock_compile.call_args.kwargs["quil"], str)

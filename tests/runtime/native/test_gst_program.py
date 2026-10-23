# Copyright 2025 qBraid
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

"""
Unit tests for submitting gate-set sequence (GST) programs to native devices.

"""
from unittest.mock import MagicMock

import pytest
from qbraid_core.services.runtime.schemas import Program

from qbraid.programs import ExperimentType, get_program_type_alias
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.runtime import DeviceStatus, TargetProfile
from qbraid.runtime.exceptions import ProgramValidationError
from qbraid.runtime.native import QbraidDevice, QbraidProvider
from qbraid.runtime.native.provider import get_program_spec_lambdas, validate_gst

DEVICE_ID = "diraq:diraq:sim:cloud-simulator"


@pytest.mark.parametrize(
    "program",
    ["Gxpi2:0@(0)", "Gxpi2:0Gcphase:0:1@(0,1)", "  Gxpi2:0Gxpi2:0@(0)\n", "(Gxpi2:0)^2@(0)"],
)
def test_gst_strings_are_detected(program):
    """GST circuits resolve to the 'gst' alias, surrounding whitespace included."""
    assert get_program_type_alias(program) == "gst"


@pytest.mark.parametrize("program", ["this is not qasm", "h q[0];", "rx(pi) q[0]"])
def test_non_gst_strings_keep_the_openqasm_error(program):
    """A string that is neither OpenQASM nor GST is not reclassified as GST."""
    with pytest.raises(ProgramTypeError, match="valid OpenQASM"):
        get_program_type_alias(program)


def test_gst_serializes_as_written():
    """GST is sent verbatim in the 'gst' format, with no wrapper class."""
    serialize = get_program_spec_lambdas("gst", DEVICE_ID)["serialize"]
    assert serialize("Gxpi2:0@(0)") == Program(format="gst", data="Gxpi2:0@(0)")


@pytest.mark.parametrize(
    "program, message",
    [
        ("Gxpi2:0", "must end with a qubit layout"),
        ("Gxpi2:0@()", "must end with a qubit layout"),
        ("Gxpi2:0@(0)\nGxpi2:1@(1)", "must be a single circuit"),
    ],
)
def test_validate_gst_rejects_what_diraq_cannot_run(program, message):
    """Diraq fails these with a generic validation error; catch them before submitting."""
    with pytest.raises(ValueError, match=message):
        validate_gst(program, DEVICE_ID)


def test_validate_gst_accepts_a_layout_circuit():
    """A single circuit ending in a qubit layout passes, surrounding whitespace included."""
    validate_gst("Gxpi2:0Gcphase:0:1@(0,1)\n", DEVICE_ID)


def _diraq_device(client: MagicMock) -> QbraidDevice:
    specs = QbraidProvider._get_program_specs(["qasm3", "gst"], DEVICE_ID)
    profile = TargetProfile(
        device_id=DEVICE_ID,
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=2,
        program_spec=specs,
        provider_name="diraq",
    )
    device = QbraidDevice(profile, client=client)
    device.status = MagicMock(return_value=DeviceStatus.ONLINE)
    return device


class _Submitted(Exception):
    """Raised by the mock client to stop after the job request is built."""


def test_device_run_submits_gst_program():
    """A device offering 'gst' sends a GST string as a 'gst' Program, untranspiled."""
    client = MagicMock()
    client.create_job.side_effect = _Submitted
    device = _diraq_device(client)

    with pytest.raises(_Submitted):
        device.run("Gxpi2:0Gcphase:0:1@(0,1)", shots=10)

    request = client.create_job.call_args.args[0]
    assert request.program == Program(format="gst", data="Gxpi2:0Gcphase:0:1@(0,1)")


def test_device_run_rejects_gst_without_layout_before_submitting():
    """The layout check runs at the default validation level, before any request."""
    client = MagicMock()
    device = _diraq_device(client)

    with pytest.raises(ProgramValidationError, match="qubit layout"):
        device.run("Gxpi2:0", shots=10)
    client.create_job.assert_not_called()

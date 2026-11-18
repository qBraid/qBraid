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
Unit tests for qBraid OS JSON programs (such as ``pulse.schedule.v1``), submitted as
qbraid-core :class:`Program` objects through :class:`QbraidProvider` devices.
"""

from unittest.mock import MagicMock

import pytest
from qbraid_core.services.runtime.schemas import Program, Result, RuntimeDevice, RuntimeJob

from qbraid.programs import get_program_type_alias
from qbraid.runtime.exceptions import ProgramValidationError
from qbraid.runtime.native import QbraidDevice, QbraidJob, QbraidProvider
from qbraid.runtime.native.provider import is_json_program_type

from .._resources import DEVICE_DATA_QIR, JOB_DATA_QIR

pytestmark = pytest.mark.skipif(
    not is_json_program_type("pulse.schedule.v1"),
    reason="JSON program types need qbraid-core 0.6.55",
)

DEVICE_ID = "qbraid_os:acme:qpu:lab-1.transmon"
QASM3 = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[1] q;\nh q[0];'
PULSE = {"instructions": [{"op": "play", "channel": "d0", "waveform": [0.1, 0.2]}]}


def _device(run_input_types: list[str]) -> tuple[QbraidDevice, MagicMock]:
    data = {
        **DEVICE_DATA_QIR["data"],
        "qrn": DEVICE_ID,
        "vendor": "qbraid_os",
        "provider": "acme",
        "deviceType": "QPU",
        "runInputTypes": run_input_types,
    }
    device_data = RuntimeDevice.model_validate(data)
    client = MagicMock()
    client.get_device.return_value = device_data
    client.create_job.return_value = MagicMock(jobQrn=f"{DEVICE_ID}-qjob-1")
    profile = QbraidProvider(client=client)._build_runtime_profile(device_data)
    return QbraidDevice(profile, client=client), client


def _sent_program(client: MagicMock) -> dict:
    return client.create_job.call_args.args[0].model_dump(mode="json")["program"]


def test_json_types_share_one_program_spec():
    """Every JSON type a device lists maps to one spec for core's Program; others are kept."""
    specs = QbraidProvider._get_program_specs(
        ["qasm3", "pulse.schedule.v1", "calibration.v1"], DEVICE_ID
    )
    assert [s.alias for s in specs] == ["qasm3", "qbraid_core"]
    assert specs[1].program_type is Program
    assert get_program_type_alias(Program(format="calibration.v1", data={})) == "qbraid_core"


@pytest.mark.parametrize("run_input_types", [["qasm3", "pulse.schedule.v1"], ["pulse.schedule.v1"]])
def test_run_sends_a_program_as_written(run_input_types):
    """run() sends a Program unchanged, also on a device that transpiles circuits to qasm3."""
    device, client = _device(run_input_types)
    device.run(Program(format="pulse.schedule.v1", data=PULSE), shots=10)
    assert _sent_program(client) == {"format": "pulse.schedule.v1", "data": PULSE}


def test_circuits_still_transpile_beside_json_types():
    """A qasm3 circuit on a device that also lists a JSON type is sent as qasm3."""
    device, client = _device(["qasm3", "pulse.schedule.v1"])
    device.run(QASM3, shots=10)
    assert _sent_program(client)["format"] == "qasm3"


def test_unlisted_json_type_is_refused_before_any_request():
    """A JSON type the device does not list is refused with the types it accepts."""
    device, client = _device(["qasm3", "pulse.schedule.v1"])
    with pytest.raises(ProgramValidationError, match="Accepted JSON program types: pulse"):
        device.run(Program(format="calibration.v1", data={}), shots=10)
    client.create_job.assert_not_called()


def test_result_keys_that_shadow_result_fields():
    """A device result with keys such as "status" or "cost" builds a Result instead of raising."""
    fit = {"routine": "rabi", "status": "converged", "cost": 0.02, "fit": {"pi_amp": 0.41}}
    client = MagicMock()
    client.get_job.return_value = RuntimeJob.model_validate(JOB_DATA_QIR)
    client.get_job_result.return_value = Result.model_validate(
        {
            "status": "COMPLETED",
            "cost": 0,
            "timeStamps": JOB_DATA_QIR["timeStamps"],
            "resultData": fit,
        }
    )
    result = QbraidJob(JOB_DATA_QIR["jobQrn"], client=client).result()
    assert result.success
    assert result.data.extra["status"] == "converged"
    assert result.data.extra["fit"] == {"pi_amp": 0.41}
    assert result.details["routine"] == "rabi"

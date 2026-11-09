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

"""
Tests for the client metadata QbraidDevice sends with a job, including ``programType``.

"""
from unittest.mock import Mock, patch

import pytest
from qbraid_core import sessions as core_sessions
from qbraid_core.services.runtime.schemas import Program

from qbraid import __version__
from qbraid.runtime import QbraidDevice

QASM2 = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nh q[0];'
QASM3 = "OPENQASM 3.0;\nqubit[1] q;\nh q[0];"
CONVERTED = Program(format="qasm3", data=QASM3)


@pytest.fixture
def device(mock_profile, mock_client) -> QbraidDevice:
    """A native device whose conversion is stubbed, recording each JobRequest it sends."""
    dev = QbraidDevice(profile=mock_profile, client=mock_client)
    dev.apply_runtime_profile = Mock(return_value=CONVERTED)
    dev.client.create_job = Mock(return_value=Mock(jobQrn="qbraid:job:1"))
    return dev


def _sent(device: QbraidDevice) -> list[dict]:
    return [call.args[0].metadata for call in device.client.create_job.call_args_list]


def test_run_records_the_type_of_the_program_passed_in(device):
    """The alias is of the user's program, not the qasm3 the device was sent."""
    device.run(QASM2, shots=10)
    assert _sent(device) == [{"programType": "qasm2"}]


def test_run_records_one_type_per_job(device):
    """A list of programs makes one job each, with that program's type."""
    device.run([QASM2, QASM3], shots=10)
    assert _sent(device) == [{"programType": "qasm2"}, {"programType": "qasm3"}]


def test_batch_job_records_one_type_or_the_sorted_types(mock_profile, mock_client):
    """A batch job of one type records a string, and of several, the sorted unique list."""
    device = QbraidDevice(
        profile=mock_profile.model_copy(update={"batch_job_support": True}), client=mock_client
    )
    device.apply_runtime_profile = Mock(return_value=CONVERTED)
    device.client.create_job = Mock(return_value=Mock(jobQrn="qbraid:job:1"))
    device.run([QASM3, QASM3], shots=10, as_batch=True)
    device.run([QASM3, QASM2, QASM3], shots=10, as_batch=True)
    assert _sent(device) == [{"programType": "qasm3"}, {"programType": ["qasm2", "qasm3"]}]


def test_batch_of_unregistered_types_records_no_program_type(mock_profile, mock_client):
    """A batch job whose programs are all of unregistered types records none."""
    device = QbraidDevice(
        profile=mock_profile.model_copy(update={"batch_job_support": True}), client=mock_client
    )
    device.apply_runtime_profile = Mock(return_value=CONVERTED)
    device.client.create_job = Mock(return_value=Mock(jobQrn="qbraid:job:1"))
    device.run([object(), object()], shots=10, as_batch=True)
    assert _sent(device) == [{}]


def test_user_metadata_is_sent_and_program_type_overrides_it(device):
    """User values pass through; the SDK's programType replaces the user's."""
    metadata = {"experiment": "e-7", "programType": "mine"}
    device.run(QASM3, shots=10, metadata=metadata)
    assert _sent(device) == [{"experiment": "e-7", "programType": "qasm3"}]
    assert metadata == {"experiment": "e-7", "programType": "mine"}


def test_direct_submit_records_no_program_type(device):
    """submit() only sees the converted program, so it records only what the user gave."""
    device.submit(CONVERTED, shots=10, metadata={"experiment": "e-7", "programType": "x"})
    device.submit(CONVERTED, shots=10)
    assert _sent(device) == [{"experiment": "e-7"}, {}]


def test_unregistered_program_type_is_not_recorded(device):
    """A program whose type is not in the registry records no programType, not the user's."""
    device.run(object(), shots=10, metadata={"programType": "x"})
    assert _sent(device) == [{}]


def test_invalid_metadata_fails_before_any_job_is_created(device):
    """A list run validates every job's request before submitting the first."""
    with pytest.raises(ValueError, match="nest at most"):
        device.run([QASM2, QASM3], shots=10, metadata={"k": _nested(40)})
    device.client.create_job.assert_not_called()


def _nested(depth: int) -> dict:
    value: dict = {}
    for _ in range(depth - 1):
        value = {"a": value}
    return value


def test_program_types_do_not_leak_into_a_later_submit(device):
    """After run() returns, a direct submit() sees no program types."""
    device.run(QASM2, shots=10)
    device.submit(CONVERTED, shots=10)
    assert _sent(device)[1] == {}


def test_sdk_registers_itself_in_the_user_agent():
    """Requests from a process that imported the SDK name it after qbraid-core."""
    assert f"qbraid/{__version__}" in core_sessions._CLIENT_TOKENS


def test_as_batch_keeps_its_positional_slot(mock_profile, mock_client):
    """``metadata`` is keyword-only, so released positional batch calls still work."""
    device = QbraidDevice(
        profile=mock_profile.model_copy(update={"batch_job_support": True}), client=mock_client
    )
    device.client.create_job = Mock(return_value=Mock(jobQrn="qbraid:job:1"))
    job = device.submit([CONVERTED, CONVERTED], 10, None, None, None, True)
    assert device.client.create_job.call_count == 1
    assert not isinstance(job, list)


def test_a_failing_type_lookup_does_not_fail_the_run(device):
    """The alias is recorded for analytics only; an error looking it up records none."""
    with patch(
        "qbraid.runtime.device.get_program_type_alias", side_effect=RuntimeError("registry")
    ):
        device.run(QASM3, shots=10)
    assert _sent(device) == [{}]

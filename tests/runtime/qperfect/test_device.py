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

"""
Unit tests for the QPerfect (MIMIQ) device.

"""

import mimiqcircuits as mc
import pytest

from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.qperfect import QPerfectJob


def test_status_online_when_connection_open(device):
    """A healthy (open) connection reports ONLINE."""
    assert device.status() == DeviceStatus.ONLINE


def test_status_offline_when_connection_not_open(device, mock_connection):
    """A connection that is not open reports OFFLINE."""
    mock_connection.connection.isOpen.return_value = False
    assert device.status() == DeviceStatus.OFFLINE


def test_status_offline_on_connection_error(device, mock_connection):
    """A connection/auth failure reports OFFLINE rather than raising."""
    mock_connection.connection.isOpen.side_effect = ConnectionError("boom")
    assert device.status() == DeviceStatus.OFFLINE


def test_submit_forwards_shots_and_options(device, mock_connection):
    """``submit`` forwards shots (nsamples), label, and MIMIQ options (incl. algorithm)."""
    circuit = mc.Circuit()
    job = device.submit(circuit, shots=512, name="myjob", algorithm="mps", bonddim=16, seed=7)

    assert isinstance(job, QPerfectJob)
    assert job.id == "exec-1"
    mock_connection.submit.assert_called_once()
    args, kwargs = mock_connection.submit.call_args
    assert args[0] is circuit
    assert kwargs["algorithm"] == "mps"
    assert kwargs["nsamples"] == 512
    assert kwargs["label"] == "myjob"
    assert kwargs["bonddim"] == 16
    assert kwargs["seed"] == 7


def test_submit_defaults_to_auto_algorithm(device, mock_connection):
    """With no algorithm option, a single-circuit submission defaults to ``algorithm='auto'``."""
    device.submit(mc.Circuit(), shots=100)
    _, kwargs = mock_connection.submit.call_args
    assert kwargs["algorithm"] == "auto"
    assert kwargs["label"] == "qbraid"
    assert kwargs["nsamples"] == 100


def test_submit_rejects_unknown_option(device):
    """An unsupported submit option raises before hitting the cloud."""
    with pytest.raises(ValueError):
        device.submit(mc.Circuit(), shots=100, not_an_option=1)


def test_submit_batch(device, mock_connection):
    """A list of circuits is submitted as a single batch job."""
    circuits = [mc.Circuit(), mc.Circuit()]
    device.submit(circuits, shots=100, algorithm="statevector")
    args, kwargs = mock_connection.submit.call_args
    assert args[0] is circuits
    assert kwargs["algorithm"] == "statevector"


def test_submit_batch_requires_explicit_algorithm(device, mock_connection):
    """MIMIQ rejects algorithm='auto' for batches, so a batch must name one itself."""
    with pytest.raises(ValueError, match="Batch submission requires an explicit algorithm"):
        device.submit([mc.Circuit(), mc.Circuit()], shots=100)
    mock_connection.submit.assert_not_called()


def test_str_names_the_device(device):
    """``str()`` shows the class and device id."""
    assert str(device) == "QPerfectDevice('mimiq-emulator')"

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
Credentialed tests that exercise the QDI provider against live QDI devices.

Two backends are covered, each skipped independently when its prerequisites
are missing:

* OQTOPUS through the in-process ``qdi-oqtopus`` client. Needs the
  ``qdi_oqtopus`` package plus ``OQTOPUS_API_TOKEN`` (and optionally
  ``OQTOPUS_BASE_URL``, defaulting to the public demo cloud).
* Any QDI HTTP endpoint, such as the qdi-demo reference server started
  locally with ``./scripts/start``. Needs ``QDI_BASE_URL`` (and
  ``QDI_AUTH_TOKEN`` for the handshake, defaulting to the demo token).

These keep the fixtures in ``conftest.py`` honest: they assert the descriptor
and result *shapes* the unit tests hard-code.

"""

import os

import pytest
import qiskit

from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.qdi import QdiDevice, QdiDeviceError, QdiJobError, QdiProvider

from .conftest import OQTOPUS_QULACS

pytestmark = pytest.mark.remote

OQTOPUS_DEMO_URL = "https://demo-api.oqtopus.io"


def _x0_circuit() -> qiskit.QuantumCircuit:
    """X on qubit 0 only: pins the bit order of the returned histogram keys."""
    circuit = qiskit.QuantumCircuit(2, 2)
    circuit.x(0)
    circuit.measure([0, 1], [0, 1])
    return circuit


@pytest.fixture(scope="module")
def oqtopus_provider():
    """A provider over the real qdi-oqtopus client, or skip."""
    pytest.importorskip("qdi_oqtopus")
    token = os.getenv("OQTOPUS_API_TOKEN")
    if not token:
        pytest.skip("OQTOPUS_API_TOKEN not set.")
    base_url = os.getenv("OQTOPUS_BASE_URL", OQTOPUS_DEMO_URL)
    return QdiProvider(
        "qdi_oqtopus.client:OqtopusQdiClient",
        credentials={"base_url": base_url, "api_token": token},
    )


@pytest.fixture(scope="module")
def qulacs(oqtopus_provider) -> QdiDevice:
    """The OQTOPUS demo simulator."""
    return oqtopus_provider.get_device("qulacs")


def test_oqtopus_descriptor_matches_fixture(oqtopus_provider):
    """The live qulacs descriptor has the shape ``conftest.OQTOPUS_QULACS`` hard-codes."""
    descriptors = {d.device_id: d for d in oqtopus_provider.discover()}
    assert "qulacs" in descriptors
    live = descriptors["qulacs"]
    assert live.supported_task_types == tuple(OQTOPUS_QULACS["supported_task_types"])
    assert live.supported_extensions == tuple(OQTOPUS_QULACS["supported_extensions"])
    assert live.supported_auth_methods == tuple(OQTOPUS_QULACS["supported_auth_methods"])
    assert live.supports_estimation is False
    assert isinstance(live.num_qubits, int)


def test_oqtopus_device_status(qulacs):
    """The demo simulator reports ready."""
    assert qulacs.status() == DeviceStatus.ONLINE


def test_oqtopus_bit_order_is_little_endian(qulacs):
    """X on qubit 0 comes back as ``'01'``: qubit 0 is the rightmost bit, qBraid's convention.

    This is the measurement the provider's pass-through of OQTOPUS counts rests
    on; if it ever flips, ``QdiJob.result`` needs ``reverse_bit_order``.
    """
    job = qulacs.run(_x0_circuit(), shots=50, extensions={"name": "qbraid-sdk-remote-test"})
    assert job.status() in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.COMPLETED}
    result = job.result()
    assert result.success is True
    assert result.data.get_counts() == {"01": 50}
    assert result.details["result_type"] == "counts"
    assert result.details["advisory"]["oqtopus_status"] == "succeeded"


def test_oqtopus_no_cancel_no_estimate(qulacs):
    """The two documented gaps (no Cancel in QDI, no estimation in OQTOPUS) raise cleanly."""
    with pytest.raises(QdiDeviceError):
        qulacs.estimate(_x0_circuit())
    job = qulacs.run(_x0_circuit(), shots=10)
    with pytest.raises(QdiJobError):
        job.cancel()


@pytest.fixture(scope="module")
def http_provider():
    """A provider over a live QDI HTTP endpoint, or skip."""
    base_url = os.getenv("QDI_BASE_URL")
    if not base_url:
        pytest.skip("QDI_BASE_URL not set.")
    token = os.getenv("QDI_AUTH_TOKEN", "valid-token")
    return QdiProvider(base_url=base_url, credentials={"token": token})


def test_http_endpoint_full_lifecycle(http_provider):
    """Discover, handshake, run, estimate, and receive over the QDI REST binding."""
    devices = http_provider.get_devices()
    assert devices, "QDI endpoint published no devices."
    device = devices[0]
    assert device.status() == DeviceStatus.ONLINE

    circuit = _x0_circuit()
    if device.profile["supports_estimation"]:
        estimate = device.estimate(circuit, shots=20)
        assert estimate["shots"] == 20

    result = device.run(circuit, shots=20).result()
    assert result.success is True
    assert sum(result.data.get_counts().values()) == 20

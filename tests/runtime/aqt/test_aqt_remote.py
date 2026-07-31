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
Remote tests for the AQT runtime, run against the live arnica API with real credentials.

These are the tests the mocked suites cannot be: they verify that the arnica payloads qBraid
actually receives still satisfy the ``aqt-connector`` models the production code reads attributes
off. A schema drift (a renamed field, a new ``ResourceStatus``, an ``available_qubits`` that turns
optional) fails here as a ``ValidationError`` naming the field, while the mocked suites keep
passing against the shape we assumed.

Skipped by default. To run:

```bash
export AQT_ACCESS_TOKEN=...           # or AQT_CLIENT_ID + AQT_CLIENT_SECRET
export AQT_ARNICA_URL=...             # optional; defaults to production arnica
export AQT_TEST_DEVICE_ID=...         # optional; "<workspace>/<resource>", defaults to the
                                      # first online simulator the token can see
pytest tests/runtime/aqt/test_aqt_remote.py --remote true
```

``test_submit_and_fetch_result_on_simulator`` submits a real (tiny, 100-shot) job to an AQT
simulator and is the only test here that consumes quota.
"""

from __future__ import annotations

import os

import pytest
from qiskit import QuantumCircuit as QiskitCircuit

from qbraid.runtime.aqt import AQTDevice, AQTProvider
from qbraid.runtime.enums import DeviceStatus, JobStatus

pytestmark = pytest.mark.remote


def _credentials_available() -> bool:
    """Whether the environment carries non-interactive AQT credentials."""
    return bool(
        os.getenv("AQT_ACCESS_TOKEN")
        or (os.getenv("AQT_CLIENT_ID") and os.getenv("AQT_CLIENT_SECRET"))
    )


skip_without_credentials = pytest.mark.skipif(
    not _credentials_available(),
    reason="Set AQT_ACCESS_TOKEN, or AQT_CLIENT_ID and AQT_CLIENT_SECRET, to run AQT remote tests.",
)


@pytest.fixture(scope="module")
def provider() -> AQTProvider:
    """A provider authenticated from the environment."""
    return AQTProvider()


@pytest.fixture(scope="module")
def simulator(provider: AQTProvider) -> AQTDevice:
    """An online AQT simulator: ``AQT_TEST_DEVICE_ID`` if set, else the first one discovered."""
    device_id = os.getenv("AQT_TEST_DEVICE_ID")
    if device_id:
        return provider.get_device(device_id)

    for device in provider.get_devices():
        if device.profile.simulator and device.status() == DeviceStatus.ONLINE:
            return device
    pytest.skip("No online AQT simulator visible to these credentials.")


@skip_without_credentials
def test_get_devices_validate_against_arnica_schema(provider: AQTProvider):
    """Every live workspace/resource payload validates and exposes the fields qBraid reads.

    ``get_devices`` already runs each payload through ``Workspace`` / ``ResourceDetails``; this
    asserts the downstream profile fields are genuinely populated, so a field that silently
    turned optional upstream is caught here rather than surfacing as ``num_qubits=None``.
    """
    devices = provider.get_devices()
    assert devices, "Expected at least one AQT resource visible to these credentials."

    for device in devices:
        assert isinstance(device, AQTDevice)
        assert device.profile.num_qubits is not None and device.profile.num_qubits > 0
        assert device.profile.get("aqt_resource_type") in {"simulator", "device"}
        assert device.id == f"{device.profile.get('aqt_workspace_id')}/{device.resource_id}"


@skip_without_credentials
def test_device_status_is_mapped(simulator: AQTDevice):
    """A live resource status maps onto a qBraid ``DeviceStatus`` (no unmapped enum member)."""
    assert simulator.status() in set(DeviceStatus)


@skip_without_credentials
def test_submit_and_fetch_result_on_simulator(simulator: AQTDevice):
    """End-to-end: transpile a Bell circuit, submit it, and read back real counts.

    Exercises the full production path — ``qiskit -> aqt_connector`` conversion, submission,
    polling, and the sample-to-counts reversal — against arnica's real result payload, which is
    the only way to confirm the bitstring ordering matches what the hardware reports.
    """
    circuit = QiskitCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure_all()

    shots = 100
    job = simulator.run(circuit, shots=shots)
    job.wait_for_final_state(timeout=600, poll_interval=5)
    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert result.success is True

    counts = result.data.get_counts()
    assert sum(counts.values()) == shots
    # A noiseless Bell state collapses to |00> / |11> only; both bits are always correlated.
    assert set(counts) <= {"00", "11"}

    execution_time = job.execution_time_s()
    assert execution_time is not None and execution_time > 0

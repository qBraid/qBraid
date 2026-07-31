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
Credentialed tests that exercise the QUDORA provider against the live Cloud API.

Skipped unless remote tests are enabled (``--remote true`` or
``QBRAID_RUN_REMOTE_TESTS=true``) and ``QUDORA_API_TOKEN`` is set. These are the tests
that keep the mocked fixtures in ``test_qudora_runtime.py`` honest: they assert the
response *shape* the unit tests hard-code, so an upstream change surfaces here rather
than as a suite that passes against a payload QUDORA no longer returns.

"""

import os

import pytest

from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.qudora import QudoraDevice, QudoraProvider

pytestmark = pytest.mark.remote

SIMULATOR_ID = "simulator-prod@qudora.com"

QASM3_X0 = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nbit[2] c;\nx q[0];\nc = measure q;'
QASM3_X1 = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nbit[2] c;\nx q[1];\nc = measure q;'

# Every key ``_build_profile`` reads, plus the ones whose absence previously went unnoticed.
REQUIRED_BACKEND_FIELDS = {
    "username",
    "user_id",
    "full_name",
    "simulator",
    "basis_gates",
    "max_n_qubits",
    "max_shots",
    "max_programs_per_job",
    "user_settings_schema",
}

# Every key ``QudoraJob`` reads off a completed job record.
REQUIRED_JOB_FIELDS = {"status", "result", "target", "user_error"}


@pytest.fixture(scope="module")
def provider():
    """A provider backed by the real QUDORA_API_TOKEN."""
    if not os.getenv("QUDORA_API_TOKEN"):
        pytest.skip("QUDORA_API_TOKEN not set.")
    return QudoraProvider()


@pytest.fixture(scope="module")
def device(provider) -> QudoraDevice:
    """The production simulator backend."""
    return provider.get_device(SIMULATOR_ID)


def test_backend_records_carry_every_field_the_profile_reads(provider):
    """The live ``/backends/`` payload contains each key ``_build_profile`` indexes.

    ``_build_profile`` previously read ``backend["id"]``, which no record has; the
    resulting ``None`` silently disabled the device status lookup.
    """
    backends = provider.session.get_backends()
    assert backends, "QUDORA published no backends."
    for backend in backends:
        assert REQUIRED_BACKEND_FIELDS <= set(backend), (
            f"backend '{backend.get('username')}' is missing "
            f"{REQUIRED_BACKEND_FIELDS - set(backend)}"
        )
        assert isinstance(backend["user_id"], int)
        assert isinstance(backend["simulator"], bool)


def test_get_devices_returns_usable_devices(provider):
    """Every listed backend builds a device whose id round-trips through get_device()."""
    devices = provider.get_devices()
    assert devices
    for dev in devices:
        assert provider.get_device(dev.id).id == dev.id
        assert dev.num_qubits > 0


def test_device_status_is_mapped(device):
    """The live BackendStatusName maps to a DeviceStatus (unmapped values raise)."""
    assert device.status() in set(DeviceStatus)


def test_available_settings_match_published_schema(device):
    """The noise parameters advertised by the device come from the live settings schema."""
    settings = device.available_settings()
    assert "measurement_error_probability" in settings
    assert settings["measurement_error_probability"]["default"] == pytest.approx(0.0035)


def test_run_single_circuit_end_to_end(device):
    """A one-circuit job completes and returns counts keyed with qubit 0 rightmost.

    ``x q[0]`` yields "01", not "10" — pinning the orientation against the real device
    rather than against a fixture that merely restates it.
    """
    job = device.run(QASM3_X0, shots=200)
    job.wait_for_final_state(timeout=180)
    assert job.status() == JobStatus.COMPLETED

    record = job.session.get_job(job.id, include_results=True)
    assert REQUIRED_JOB_FIELDS <= set(
        record
    ), f"job record is missing {REQUIRED_JOB_FIELDS - set(record)}"

    result = job.result()
    assert result.success is True
    assert result.device_id == device.id
    counts = result.data.measurement_counts
    assert max(counts, key=counts.get) == "01"
    assert sum(counts.values()) == 200


def test_run_batch_returns_one_histogram_per_program(device):
    """A batch job returns a list of histograms, one per submitted program, in order."""
    job = device.run([QASM3_X0, QASM3_X1], shots=100)
    job.wait_for_final_state(timeout=180)

    counts = job.result().data.measurement_counts
    assert isinstance(counts, list) and len(counts) == 2
    assert max(counts[0], key=counts[0].get) == "01"
    assert max(counts[1], key=counts[1].get) == "10"


def test_cancel_job(device):
    """A submitted job can be cancelled and reports CANCELLED afterwards."""
    job = device.run(QASM3_X0, shots=100)
    job.cancel()
    job.wait_for_final_state(timeout=180)
    assert job.status() == JobStatus.CANCELLED

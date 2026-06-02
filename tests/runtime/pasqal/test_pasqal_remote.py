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
Remote integration tests for Pasqal provider, device, and job classes.

These tests submit real jobs to the Pasqal Cloud EMU_FREE emulator and verify
end-to-end result flow.
"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("pasqal_cloud")
pytest.importorskip("pulser")

# pylint: disable=wrong-import-position
from pulser import Pulse, Register, Sequence  # noqa: E402
from pulser.devices import AnalogDevice  # noqa: E402

from qbraid._logging import logger  # noqa: E402
from qbraid.runtime.enums import DeviceStatus, JobStatus  # noqa: E402
from qbraid.runtime.pasqal import PasqalDevice, PasqalJob, PasqalProvider  # noqa: E402
from qbraid.runtime.result import Result  # noqa: E402
from qbraid.runtime.result_data import AnalogResultData  # noqa: E402

TIMEOUT = 600
DEVICE_ID = "EMU_FREE"


def _get_credentials() -> dict[str, str]:
    """Return Pasqal credentials from environment, skipping if unset."""
    username = os.getenv("PASQAL_USERNAME")
    password = os.getenv("PASQAL_PASSWORD")
    project_id = os.getenv("PASQAL_PROJECT_ID")
    if not username or not password or not project_id:
        pytest.skip("PASQAL_USERNAME, PASQAL_PASSWORD, or PASQAL_PROJECT_ID is not set")
    return {"username": username, "password": password, "project_id": project_id}


def _make_sequence() -> Sequence:
    """Create a simple 2-qubit Pulser sequence with a global Rydberg pulse."""
    qubits = {"q0": (0, 0), "q1": (0, 10)}
    reg = Register(qubits)
    seq = Sequence(reg, AnalogDevice)
    seq.declare_channel("rydberg_global", "rydberg_global")
    pulse = Pulse.ConstantPulse(duration=1000, amplitude=5.0, detuning=0, phase=0)
    seq.add(pulse, "rydberg_global")
    seq.measure("ground-rydberg")
    return seq


def _wait_or_skip(job: PasqalJob) -> None:
    """Wait for a job to finish, skip the test on timeout."""
    try:
        job.wait_for_final_state(timeout=TIMEOUT)
    except TimeoutError as err:
        logger.error(err)
        pytest.skip(f"Job {job.id} did not complete within {TIMEOUT}s timeout")


# ---------------------------------------------------------------------------
# Provider / device discovery
# ---------------------------------------------------------------------------


@pytest.mark.remote
def test_provider_get_devices():
    """Provider can list available devices."""
    creds = _get_credentials()
    provider = PasqalProvider(**creds)
    devices = provider.get_devices()
    assert len(devices) > 0
    assert all(isinstance(d, PasqalDevice) for d in devices)


@pytest.mark.remote
def test_provider_get_device():
    """Provider can retrieve EMU_FREE emulator device."""
    creds = _get_credentials()
    provider = PasqalProvider(**creds)
    device = provider.get_device(DEVICE_ID)
    assert isinstance(device, PasqalDevice)
    assert device.id == DEVICE_ID


@pytest.mark.remote
def test_device_status():
    """Device status is ONLINE for the EMU_FREE emulator."""
    creds = _get_credentials()
    provider = PasqalProvider(**creds)
    device = provider.get_device(DEVICE_ID)
    assert device.status() == DeviceStatus.ONLINE


# ---------------------------------------------------------------------------
# Single sequence submission via device.run()
# ---------------------------------------------------------------------------


@pytest.mark.remote
def test_single_sequence_run():
    """Submit a single Pulser sequence via device.run() and verify result."""
    creds = _get_credentials()
    provider = PasqalProvider(**creds)
    device = provider.get_device(DEVICE_ID)

    seq = _make_sequence()
    job = device.run(seq, shots=50)

    assert isinstance(job, PasqalJob)

    _wait_or_skip(job)

    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, Result)
    assert result.success is True
    assert result.device_id == DEVICE_ID
    assert result.job_id == job.id

    data = result.data
    assert isinstance(data, AnalogResultData)

    counts = data.get_counts()
    assert counts is not None
    assert isinstance(counts, dict)
    assert len(counts) > 0
    assert sum(counts.values()) == 50


# ---------------------------------------------------------------------------
# Job status polling
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def completed_job_context():
    """Submit one job and return its ID, provider, and device for reuse."""
    creds = _get_credentials()
    provider = PasqalProvider(**creds)
    device = provider.get_device(DEVICE_ID)

    seq = _make_sequence()
    job = device.run(seq, shots=50)

    try:
        job.wait_for_final_state(timeout=TIMEOUT)
    except TimeoutError:
        pytest.skip("Shared job did not complete in time")

    return {
        "job_id": job.id,
        "provider": provider,
        "device": device,
        "sdk": provider.sdk,
    }


@pytest.mark.remote
def test_completed_job_status(completed_job_context):
    """Completed job reports COMPLETED status."""
    sdk = completed_job_context["sdk"]
    job_id = completed_job_context["job_id"]
    device = completed_job_context["device"]

    reconstructed = PasqalJob(job_id=job_id, sdk=sdk, device=device)
    assert reconstructed.status() == JobStatus.COMPLETED


@pytest.mark.remote
def test_completed_job_result(completed_job_context):
    """Completed job returns valid AnalogResultData with counts."""
    sdk = completed_job_context["sdk"]
    job_id = completed_job_context["job_id"]
    device = completed_job_context["device"]

    reconstructed = PasqalJob(job_id=job_id, sdk=sdk, device=device)
    result = reconstructed.result()

    assert result.success is True
    assert result.device_id == DEVICE_ID
    assert isinstance(result.data, AnalogResultData)

    counts = result.data.get_counts()
    assert counts is not None
    assert isinstance(counts, dict)
    assert len(counts) > 0

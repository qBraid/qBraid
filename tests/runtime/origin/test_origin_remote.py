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

# pylint: disable=expression-not-assigned,import-outside-toplevel

"""
Remote integration tests for OriginQ provider, device, and job classes.

These tests submit real jobs to the OriginQ QCloud simulator and verify
end-to-end result flow.
"""
from __future__ import annotations

import os

import pytest

from qbraid._logging import logger
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.origin import OriginDevice, OriginJob, OriginProvider
from qbraid.runtime.origin.job import OriginJobError
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

TIMEOUT = 600
BACKEND_ID = "full_amplitude"


def _get_api_key() -> str:
    key = os.getenv("ORIGIN_API_KEY")
    if not key:
        pytest.skip("ORIGIN_API_KEY is not set")
    return key


def _make_bell_program():
    """Create a simple Bell state QProg (2-qubit, measured)."""
    from pyqpanda3.core import CNOT, H, QProg, measure

    prog = QProg(2)
    q = prog.qubits()
    prog << H(q[0]) << CNOT(q[0], q[1]) << measure(0, 0) << measure(1, 1)
    return prog


def _wait_or_skip(job: OriginJob) -> None:
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
    api_key = _get_api_key()
    provider = OriginProvider(api_key=api_key)
    devices = provider.get_devices()
    assert len(devices) > 0
    assert all(isinstance(d, OriginDevice) for d in devices)


@pytest.mark.remote
def test_provider_get_device():
    """Provider can retrieve a specific simulator device."""
    api_key = _get_api_key()
    provider = OriginProvider(api_key=api_key)
    device = provider.get_device(BACKEND_ID)
    assert isinstance(device, OriginDevice)
    assert device.id == BACKEND_ID


@pytest.mark.remote
def test_device_status():
    """Device status is ONLINE for the full_amplitude simulator."""
    api_key = _get_api_key()
    provider = OriginProvider(api_key=api_key)
    device = provider.get_device(BACKEND_ID)
    assert device.status() == DeviceStatus.ONLINE


# ---------------------------------------------------------------------------
# Single circuit submission via device.run()
# ---------------------------------------------------------------------------


@pytest.mark.remote
def test_single_circuit_run():
    """Submit a single QProg via device.run() and verify result."""
    api_key = _get_api_key()
    provider = OriginProvider(api_key=api_key)
    device = provider.get_device(BACKEND_ID)

    prog = _make_bell_program()
    job = device.run(prog, shots=1000)

    assert isinstance(job, OriginJob)

    _wait_or_skip(job)

    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, Result)
    assert result.success is True
    assert result.device_id == BACKEND_ID
    assert result.job_id == job.id

    data = result.data
    assert isinstance(data, GateModelResultData)

    probs = data.get_probabilities()
    assert probs is not None
    assert isinstance(probs, dict)
    assert len(probs) > 0
    assert all(isinstance(v, float) for v in probs.values())


# ---------------------------------------------------------------------------
# Batch circuit submission via device.run()
# ---------------------------------------------------------------------------


@pytest.mark.remote
def test_batch_circuit_run_simulator():
    """Submit a list of QProgs on a simulator; returns a list of individual jobs."""
    api_key = _get_api_key()
    provider = OriginProvider(api_key=api_key)
    device = provider.get_device(BACKEND_ID)

    prog1 = _make_bell_program()
    prog2 = _make_bell_program()
    jobs = device.run([prog1, prog2], shots=1000)

    assert isinstance(jobs, list)
    assert len(jobs) == 2
    assert all(isinstance(j, OriginJob) for j in jobs)

    for job in jobs:
        _wait_or_skip(job)
        assert job.status() == JobStatus.COMPLETED

        result = job.result()
        assert isinstance(result, Result)
        assert result.success is True
        assert isinstance(result.data, GateModelResultData)

        probs = result.data.get_probabilities()
        assert probs is not None
        assert isinstance(probs, dict)


# ---------------------------------------------------------------------------
# Direct device construction (not from provider)
# ---------------------------------------------------------------------------


@pytest.mark.remote
def test_device_direct_construction():
    """Create an OriginDevice directly without going through OriginProvider."""
    api_key = _get_api_key()

    from qbraid.programs import ExperimentType, ProgramSpec
    from qbraid.runtime.origin.provider import SIMULATOR_BACKENDS, _get_service
    from qbraid.runtime.profile import TargetProfile

    service = _get_service(api_key)
    backend = service.backend(BACKEND_ID)

    from pyqpanda3.core import QProg

    profile = TargetProfile(
        device_id=BACKEND_ID,
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=SIMULATOR_BACKENDS[BACKEND_ID],
        program_spec=ProgramSpec(QProg, alias="pyqpanda3"),
        provider_name="origin",
    )

    device = OriginDevice(profile=profile, backend=backend, service=service)
    assert device.id == BACKEND_ID

    prog = _make_bell_program()
    job = device.run(prog, shots=100)
    _wait_or_skip(job)

    result = job.result()
    assert result.success is True
    assert result.device_id == BACKEND_ID


# ---------------------------------------------------------------------------
# Direct job construction — various parameter combos
#
# These tests share a single submitted job to avoid redundant waiting.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def completed_job_context():
    """Submit one job and return its ID, provider, and device for reuse."""
    api_key = _get_api_key()
    provider = OriginProvider(api_key=api_key)
    device = provider.get_device(BACKEND_ID)

    prog = _make_bell_program()
    job = device.run(prog, shots=100)

    try:
        job.wait_for_final_state(timeout=TIMEOUT)
    except TimeoutError:
        pytest.skip("Shared job did not complete in time")

    return {
        "job_id": job.id,
        "provider": provider,
        "device": device,
    }


@pytest.mark.remote
def test_job_from_id_only(completed_job_context):
    """Reconstruct an OriginJob from just a job ID."""
    job_id = completed_job_context["job_id"]

    reconstructed = OriginJob(job_id=job_id)

    assert reconstructed.id == job_id
    assert reconstructed.status() == JobStatus.COMPLETED
    result = reconstructed.result()
    assert result.success is True
    assert result.device_id == "origin"  # no device attached


@pytest.mark.remote
def test_job_from_id_and_device(completed_job_context):
    """Reconstruct an OriginJob with job_id and device."""
    job_id = completed_job_context["job_id"]
    device = completed_job_context["device"]

    reconstructed = OriginJob(job_id=job_id, device=device)

    assert reconstructed.status() == JobStatus.COMPLETED
    result = reconstructed.result()
    assert result.device_id == BACKEND_ID


@pytest.mark.remote
def test_job_from_id_and_service(completed_job_context):
    """Reconstruct an OriginJob with job_id and service."""
    job_id = completed_job_context["job_id"]
    provider = completed_job_context["provider"]

    reconstructed = OriginJob(job_id=job_id, service=provider.service)

    assert reconstructed.status() == JobStatus.COMPLETED
    result = reconstructed.result()
    assert result.success is True


@pytest.mark.remote
def test_job_from_id_device_and_service(completed_job_context):
    """Reconstruct an OriginJob with job_id, device, and service."""
    job_id = completed_job_context["job_id"]
    device = completed_job_context["device"]
    provider = completed_job_context["provider"]

    reconstructed = OriginJob(job_id=job_id, device=device, service=provider.service)

    assert reconstructed.status() == JobStatus.COMPLETED
    result = reconstructed.result()
    assert result.device_id == BACKEND_ID
    assert result.success is True


# ---------------------------------------------------------------------------
# Job cancel (unsupported)
# ---------------------------------------------------------------------------


@pytest.mark.remote
def test_cancel_raises(completed_job_context):
    """OriginQ jobs cannot be cancelled."""
    job_id = completed_job_context["job_id"]
    reconstructed = OriginJob(job_id=job_id)

    with pytest.raises(OriginJobError, match="does not support"):
        reconstructed.cancel()


# ---------------------------------------------------------------------------
# Result metadata
# ---------------------------------------------------------------------------


@pytest.mark.remote
def test_result_metadata(completed_job_context):
    """Result carries through OriginQ task metadata."""
    job_id = completed_job_context["job_id"]
    reconstructed = OriginJob(job_id=job_id)

    result = reconstructed.result()
    details = result._details
    assert "obj" in details
    assert details["obj"]["taskId"] == job_id

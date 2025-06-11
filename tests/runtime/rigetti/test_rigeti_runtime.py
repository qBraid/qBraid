# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint:disable=redefined-outer-name
"""
Unit tests for Rigetti runtime

"""
from unittest.mock import Mock, patch

import pyquil
import pytest
from pyquil import Program
from qcs_sdk import QCSClient
from qcs_sdk.qpu.api import QpuApiError, SubmissionError
from qcs_sdk.qpu.isa import GetISAError

from qbraid.programs.experiment import ExperimentType
from qbraid.runtime import GateModelResultData, Result, TargetProfile
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.rigetti import RigettiDevice, RigettiJob, RigettiProvider
from qbraid.runtime.rigetti.job import RigettiJobError

DEVICE_ID = "Ankaa-3"


@pytest.fixture
def target_profile():
    return TargetProfile(
        device_id=DEVICE_ID,
        simulator=False,
        experiment_type=ExperimentType.GATE_MODEL,
        program_spec=None,
        num_qubits=32,
        provider_name="rigetti",
    )


@pytest.fixture
def rigetti_device(target_profile):
    with patch("qbraid.runtime.rigetti.device.get_qc") as mock_get_qc:
        qc = Mock()
        qc.qubits.return_value = [0, 1, 2]
        mock_get_qc.return_value = qc
        mock_qubits = {
            0: Mock(id=0, dead=False),
            1: Mock(id=1, dead=False),
            2: Mock(id=2, dead=True),
        }
        qc.to_compiler_isa.return_value.qubits = mock_qubits
        compiled = Mock()
        qc.compile.return_value = compiled
        qam = Mock()
        qc.qam = qam
        qam.execute.return_value = Mock(job_id="job-123")

        yield RigettiDevice(
            profile=target_profile,
            qcs_client=None,  # Mocked in tests
        )


@pytest.fixture
def simulator_profile():
    return TargetProfile(
        device_id=DEVICE_ID,
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        program_spec=None,
        num_qubits=32,
        provider_name="rigetti",
    )


def test_rigetti_provider_init(monkeypatch):
    # Patch QCSClient and env
    with (
        patch("os.getenv") as mock_getenv,
        patch("qcs_sdk.client.AuthServer"),
        patch("qcs_sdk.client.OAuthSession"),
        patch("qcs_sdk.client.RefreshToken"),
        patch("pyquil.api.QCSClient"),
    ):
        mock_getenv.side_effect = lambda k: "x"  # Return dummy for all env vars
        provider = RigettiProvider(qcs_client=None, as_qvm=False)
        assert isinstance(provider, RigettiProvider)


@pytest.fixture(scope="session")
def client_configuration() -> QCSClient:
    return QCSClient.load()


def test_build_profile_qvm():
    provider = RigettiProvider(qcs_client=None, as_qvm=True)
    with patch("qbraid.runtime.rigetti.provider.get_qc") as mock_get_qc:
        qc = Mock()
        qc.qubits.return_value = [0, 1, 2]
        mock_get_qc.return_value = qc
        profile = provider._build_profile(DEVICE_ID)
        assert profile.device_id == DEVICE_ID
        assert profile.simulator is True
        assert profile.num_qubits == 3


def test_build_profile_qpu(client_configuration):
    provider = RigettiProvider(qcs_client=client_configuration, as_qvm=False)
    mock_isa = Mock()
    mock_isa.name = DEVICE_ID
    mock_isa.architecture.nodes = [0, 1, 2, 3]
    # Patch *the function* so it doesn't care what client is (avoids Rust type error)
    with patch(
        "qbraid.runtime.rigetti.provider.get_instruction_set_architecture", return_value=mock_isa
    ):
        profile = provider._build_profile(DEVICE_ID)
        assert profile.device_id == DEVICE_ID
        assert profile.simulator is False
        assert profile.num_qubits == 4


def test_get_devices(target_profile):
    provider = RigettiProvider(qcs_client=None, as_qvm=True)
    with (
        patch("qbraid.runtime.rigetti.provider.list_quantum_processors", return_value=[DEVICE_ID]),
        patch(
            "qbraid.runtime.rigetti.provider.RigettiProvider._build_profile"
        ) as mock_build_profile,
        patch("qbraid.runtime.rigetti.device.get_qc", return_value=Mock()),
    ):
        mock_build_profile.return_value = target_profile
        devices = provider.get_devices()
        assert isinstance(devices, list)
        assert isinstance(devices[0], RigettiDevice)


def test_get_device(client_configuration):
    provider = RigettiProvider(qcs_client=client_configuration, as_qvm=True)
    with (
        patch("qbraid.runtime.rigetti.device.get_qc") as mock_get_qc,
        patch("qbraid.runtime.rigetti.provider.get_qc") as mock_get_qc_1,
    ):
        mock_get_qc.return_value.qubits.return_value = [0, 1, 2]
        mock_get_qc_1.return_value.qubits.return_value = [0, 1, 2]
        device = provider.get_device(DEVICE_ID)
        assert isinstance(device, RigettiDevice)


def test_rigetti_device_status_online(rigetti_device):
    with (
        patch(
            "qbraid.runtime.rigetti.device.get_instruction_set_architecture", return_value=Mock()
        ),
    ):
        assert rigetti_device.status() == DeviceStatus.ONLINE


def test_rigetti_device_status_offline(rigetti_device):
    with patch(
        "qbraid.runtime.rigetti.device.get_instruction_set_architecture",
        side_effect=GetISAError("fail"),
    ):
        assert rigetti_device.status() == DeviceStatus.OFFLINE


def test_rigetti_device_status_simulator(simulator_profile):
    with patch("qbraid.runtime.rigetti.device.get_qc") as mock_get_qc:
        qc = Mock()
        mock_get_qc.return_value = qc
        device = RigettiDevice(profile=simulator_profile, qcs_client=None)
        assert device.status() == DeviceStatus.ONLINE


def test_live_qubits(rigetti_device):
    live = rigetti_device.live_qubits()
    assert set(live) == {0, 1}


def test_device_submit_and_submit_batch(rigetti_device):
    prog = Program("H 0")
    job = rigetti_device.submit(prog)
    assert isinstance(job, RigettiJob)
    jobs = rigetti_device.submit([prog, prog])
    assert isinstance(jobs, list)
    assert isinstance(jobs[0], RigettiJob)


def test_rigetti_job_status_and_cancel(rigetti_device):
    qam = Mock()
    execute_response = Mock()
    rigetti_device._qc.qam = qam
    job = RigettiJob(job_id="job-1", device=rigetti_device, execute_response=execute_response)
    assert job.status() == JobStatus.RUNNING
    # Cancel QPU
    with patch.object(qam, "__class__", pyquil.api.QPU):
        qam.cancel.return_value = None
        job.cancel()
        assert job.status() in (JobStatus.CANCELLING, JobStatus.CANCELLED)


def test_rigetti_job_cancel_simulator(rigetti_device):
    qam = Mock()
    execute_response = Mock()
    rigetti_device._qc.qam = qam
    job = RigettiJob(job_id="job-1", device=rigetti_device, execute_response=execute_response)
    # Not a QPU (e.g., QVM)
    job.cancel()  # Should warn, but not fail


def test_rigetti_job_get_result_counts(rigetti_device):
    qam = Mock()
    execute_response = Mock()
    qam.get_result.return_value.get_register_map.return_value = {"ro": [[0, 1], [1, 0], [0, 1]]}
    rigetti_device._qc.qam = qam
    job = RigettiJob(job_id="job-1", device=rigetti_device, execute_response=execute_response)
    result = job.get_result()
    assert "counts" in result
    assert "probabilities" in result
    assert sum(result["counts"].values()) == 3


def test_rigetti_job_result_success(rigetti_device):
    qam = Mock()
    execute_response = Mock()
    qam.get_result.return_value.get_register_map.return_value = {"ro": [[0, 1], [1, 0], [0, 1]]}
    rigetti_device._qc.qam = qam
    job = RigettiJob(job_id="job-1", device=rigetti_device, execute_response=execute_response)
    res = job.result()
    assert isinstance(res, Result)
    assert isinstance(res.data, GateModelResultData)
    assert res.success is True


def test_rigetti_job_result_failure(rigetti_device):
    qam = Mock()
    execute_response = Mock()
    qam.get_result.side_effect = QpuApiError()
    rigetti_device._qc.qam = qam
    job = RigettiJob(job_id="job-1", device=rigetti_device, execute_response=execute_response)

    res = job.result()
    assert res.success is False


def test_rigetti_job_error_in_submit(rigetti_device):
    mock_qc = Mock()
    mock_qc.compile.return_value = "compiled"
    qam = Mock()
    mock_qc.qam = qam
    qam.execute.side_effect = SubmissionError()
    rigetti_device._qc = mock_qc

    with pytest.raises(RigettiJobError):
        rigetti_device.submit(Program("X 0"))


def test_device_str_repr(rigetti_device):
    assert "RigettiDevice" in str(rigetti_device)
    assert rigetti_device.profile.device_id in str(rigetti_device)

# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for IonQProvider class

"""
from unittest.mock import Mock, patch

import pytest

from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
from qbraid.runtime import GateModelResultData, Result, TargetProfile
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.ionq import IonQDevice, IonQJob, IonQProvider, IonQSession
from qbraid.runtime.ionq.job import IonQJobError
from qbraid.runtime.ionq.provider import SUPPORTED_GATES

FIXTURE_COUNT = sum(key in NATIVE_REGISTRY for key in ["qiskit", "braket", "cirq"])

DEVICE_DATA = [
    {
        "backend": "qpu.harmony",
        "status": "available",
        "qubits": 11,
        "average_queue_time": 1352464532,
        "last_updated": 1717253790,
        "has_access": False,
        "characterization_url": "/characterizations/ab9ff65b-693f-417f-a07b-927b3e48f6e6",
        "degraded": False,
    },
    {
        "backend": "qpu.aria-1",
        "status": "available",
        "qubits": 25,
        "average_queue_time": 136598879,
        "last_updated": 1717253790,
        "has_access": False,
        "characterization_url": "/characterizations/8c04e925-76fe-4ff6-83f3-9daf643abbf0",
        "degraded": False,
    },
    {
        "backend": "qpu.aria-2",
        "status": "available",
        "qubits": 25,
        "average_queue_time": 1449545843,
        "last_updated": 1717253790,
        "has_access": False,
        "characterization_url": "/characterizations/b652694a-912c-47a8-8a67-f6edfd3c6bb2",
        "degraded": False,
    },
    {
        "backend": "qpu.forte-1",
        "status": "available",
        "qubits": 36,
        "average_queue_time": 1533413000,
        "last_updated": 1717253790,
        "has_access": False,
        "characterization_url": "/characterizations/4e8623ac-d592-4763-a3b6-ad8de775b735",
        "degraded": False,
    },
    {
        "backend": "simulator",
        "status": "available",
        "qubits": 29,
        "average_queue_time": 0,
        "last_updated": 1717253790,
        "has_access": True,
        "noise_models": ["aria-1", "harmony", "ideal"],
        "degraded": False,
    },
]

POST_JOB_RESPONSE = {
    "id": "c86a043a-6aea-47cf-b3a6-70ab1e538cab",
    "status": "ready",
    "request": 1717311751,
}

GET_JOB_RESPONSE = {
    "id": "c86a043a-6aea-47cf-b3a6-70ab1e538cab",
    "submitted_by": "e1254d93988e405e80d7842a",
    "status": "completed",
    "target": "simulator",
    "qubits": 1,
    "circuits": 1,
    "results_url": "/v0.3/jobs/c86a043a-6aea-47cf-b3a6-70ab1e538cab/results",
    "gate_counts": {"1q": 1, "2q": 0},
    "cost_usd": 0,
    "project_id": "0c2ac5b4-6078-40a0-9574-91f7aeab0b7e",
    "request": 1717296868,
    "start": 1717296869,
    "response": 1717296869,
    "execution_time": 39,
    "predicted_execution_time": 2,
    "noise": {"model": "ideal"},
    "error_mitigation": {"debias": False},
    "children": [],
}

GET_JOB_RESULT_RESPONSE = {"0": 0.5, "1": 0.5}


def test_ionq_provider_get_device():
    """Test getting IonQ provider and device."""
    with patch("qbraid.runtime.ionq.provider.Session") as mock_session:
        mock_session.return_value.get.return_value.json.return_value = DEVICE_DATA

        provider = IonQProvider(api_key="fake_api_key")
        assert isinstance(provider, IonQProvider)
        assert isinstance(provider.session, IonQSession)
        assert provider.session.api_key == "fake_api_key"
        assert provider.session.base_url == "https://api.ionq.co/v0.3"
        assert provider.session.headers["Content-Type"] == "application/json"
        assert provider.session.headers["Authorization"] == "apiKey fake_api_key"

        test_devices = provider.get_devices()
        assert isinstance(test_devices, list)
        for test_device in test_devices:
            assert isinstance(test_device, IonQDevice)
            assert test_device.profile["device_id"] in [device["backend"] for device in DEVICE_DATA]
            assert test_device.profile["simulator"] is False or test_device.id == "simulator"
            assert test_device.profile["num_qubits"] in [device["qubits"] for device in DEVICE_DATA]
            assert test_device.profile["program_spec"] == ProgramSpec(str, alias="qasm2")

        test_device = provider.get_device("qpu.harmony")
        assert isinstance(test_device, IonQDevice)
        assert test_device.profile["device_id"] == "qpu.harmony"
        assert test_device.profile["simulator"] is False
        assert test_device.profile["num_qubits"] == 11
        assert test_device.profile["program_spec"] == ProgramSpec(str, alias="qasm2")
        assert test_device.profile["basis_gates"] == set(SUPPORTED_GATES)


def test_ionq_provider_device_unavailable():
    """Test getting IonQ provider and different status devices."""

    class MockSession:
        """Mock session class."""

        def get_device(self, device_id: str):
            """Mock get_device method."""
            res = DEVICE_DATA[0]
            if device_id == "qpu.harmony":
                res["status"] = "unavailable"
            elif device_id == "qpu.aria-1":
                res["status"] = "offline"
            elif device_id == "qpu.aria-2":
                res["status"] = "available"
            elif device_id == "fake_device":
                res["status"] = "fake_status"
            return res

    unavailable_profile = TargetProfile(device_id="qpu.harmony", simulator=False)
    unavailable_device = IonQDevice(unavailable_profile, MockSession())
    assert unavailable_device.status() == DeviceStatus.UNAVAILABLE

    offline_profile = TargetProfile(device_id="qpu.aria-1", simulator=False)
    offline_device = IonQDevice(offline_profile, MockSession())
    assert offline_device.status() == DeviceStatus.OFFLINE

    available_profile = TargetProfile(device_id="qpu.aria-2", simulator=False)
    available_device = IonQDevice(available_profile, MockSession())
    assert available_device.status() == DeviceStatus.ONLINE

    fake_profile = TargetProfile(device_id="fake_device", simulator=False)
    fake_device = IonQDevice(fake_profile, MockSession())
    with pytest.raises(ValueError):
        fake_device.status()


def test_ionq_device_transform_run_input():
    """Test transforming OpenQASM 2 string to supported gates + json format."""
    qasm_input = """
    OPENQASM 2.0;
    qreg q[2];
    cry(pi/4) q[0], q[1];
    """
    expected_output = {
        "qubits": 2,
        "circuit": [
            {"gate": "ry", "target": 1, "rotation": 0.39269908169872414},
            {"gate": "cnot", "control": 0, "target": 1},
            {"gate": "ry", "target": 1, "rotation": -0.39269908169872414},
            {"gate": "cnot", "control": 0, "target": 1},
        ],
    }

    with patch("qbraid_core.sessions.Session") as mock_session:
        mock_session.return_value.get.return_value.json.return_value = DEVICE_DATA

        provider = IonQProvider(api_key="fake_api_key")
        test_devices = provider.get_devices()
        device = test_devices[0]
        program_json = device.transform(qasm_input)
        assert program_json == expected_output

        dummy_provider = IonQProvider(api_key="fake_api_key")
        assert provider == dummy_provider


@pytest.mark.parametrize("circuit", range(FIXTURE_COUNT), indirect=True)
@patch("qbraid_core.sessions.Session.get")
@patch("qbraid_core.sessions.Session.post")
def test_ionq_device_run_submit_job(mock_post, mock_get, circuit):
    """Test running a fake job."""
    mock_get_response = Mock()
    mock_get_response.json.side_effect = [
        DEVICE_DATA,  # provider.get_device("simulator")
        DEVICE_DATA,  # ionq_device.run(circuit, shots=2)
        GET_JOB_RESPONSE,  # job.status()
        GET_JOB_RESPONSE,  # job.metadata()
        GET_JOB_RESPONSE,  # job.result()
        GET_JOB_RESULT_RESPONSE,  # job.result()
    ]
    mock_get.return_value = mock_get_response

    # Setup mock for post
    mock_post_response = Mock()
    mock_post_response.json.return_value = POST_JOB_RESPONSE
    mock_post.return_value = mock_post_response

    provider = IonQProvider(api_key="fake_api_key")
    ionq_device = provider.get_device("simulator")
    job = ionq_device.run(circuit, shots=2)
    assert isinstance(job, IonQJob)

    job_status = job.status()
    assert isinstance(job_status, JobStatus)
    assert job_status == JobStatus.COMPLETED

    job_metadata = job.metadata()
    assert isinstance(job_metadata, dict)
    assert job_metadata["job_id"] == "c86a043a-6aea-47cf-b3a6-70ab1e538cab"
    assert job_metadata["shots"] == 2
    assert job_metadata["status"] == JobStatus.COMPLETED

    res = job.result()
    assert isinstance(res, Result)
    assert isinstance(res.data, GateModelResultData)
    assert res.data.get_counts() == {"0": 1, "1": 1}
    assert res.data.measurements is None


@pytest.mark.parametrize("circuit", range(FIXTURE_COUNT), indirect=True)
@patch("qbraid_core.sessions.Session.get")
@patch("qbraid_core.sessions.Session.post")
def test_ionq_failed_job(mock_post, mock_get, circuit):
    """Test running a fake job."""
    GET_JOB_RESPONSE["status"] = "failed"
    mock_get_response = Mock()
    mock_get_response.json.side_effect = [
        DEVICE_DATA,  # provider.get_device("simulator")
        DEVICE_DATA,  # ionq_device.run(circuit, shots=2)
        {"status": "failed"},  # job.status()
        GET_JOB_RESPONSE,  # job.metadata()
        GET_JOB_RESPONSE,  # job.result()
        GET_JOB_RESULT_RESPONSE,  # job.result()
    ]
    mock_get.return_value = mock_get_response

    # Setup mock for post
    mock_post_response = Mock()
    mock_post_response.json.return_value = POST_JOB_RESPONSE
    mock_post.return_value = mock_post_response

    provider = IonQProvider(api_key="fake_api_key")
    ionq_device = provider.get_device("simulator")
    job = ionq_device.run(circuit, shots=2)
    assert isinstance(job, IonQJob)

    job_status = job.status()
    assert isinstance(job_status, JobStatus)
    assert job_status == JobStatus.FAILED

    with pytest.raises(IonQJobError):
        job.result()


def test_ionq_job_cancel():
    """Test cancelling a job."""

    class FakeSession:
        """Fake session class."""

        def cancel_job(self, job_id: str):  # pylint: disable=unused-argument
            """Fake cancel job."""
            return None

    job = IonQJob("fake_job_id", FakeSession())
    assert job.cancel() is None


def test_ionq_session_cancel():
    """Test cancelling a job."""
    with patch("qbraid_core.sessions.Session.put") as mock_put:
        mock_put.return_value.json.return_value = None

        session = IonQSession(api_key="fake_api_key")
        assert session.cancel_job("fake_job_id") is None


def test_ionq_submit_fail():
    """Test submitting a job that fails."""
    circuit = """
    OPENQASM 2.0;
    qreg q[2];
    ry(pi/4) q[0];
    """
    device = IonQDevice(
        TargetProfile(device_id="simulator", simulator=False),
        IonQSession("fake_api_key"),
    )
    with patch("qbraid_core.sessions.Session.post") as mock_post:
        mock_post.return_value.json.return_value = {"error": "fake_error"}

        with pytest.raises(ValueError):
            device.run(circuit, shots=2)


@pytest.mark.parametrize("result", [{"probabilities": {"0": 0.5, "1": 0.5}}, {"shots": 100}])
def test_get_counts_raises_value_error_for_missing_data(result):
    """Test that _get_counts raises a ValueError if shots or probabilities are missing."""
    with pytest.raises(ValueError) as exc_info:
        IonQJob._get_counts(result)
    assert "Missing shots or probabilities in result data." in str(exc_info.value)


@pytest.fixture
def mock_ionq_provider():
    """Return a mock IonQProvider instance."""
    return IonQProvider(api_key="mock_api_key")


@patch("builtins.hash", autospec=True)
def test_hash_method_creates_and_returns_hash(mock_hash, mock_ionq_provider):
    """Test that the __hash__ method creates and returns a hash."""
    mock_hash.return_value = 7777
    provider_instance = mock_ionq_provider
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    mock_hash.assert_called_once_with(("mock_api_key", "https://api.ionq.co/v0.3"))
    assert result == 7777
    assert provider_instance._hash == 7777


def test_hash_method_returns_existing_hash(mock_ionq_provider):
    """Test that the __hash__ method returns an existing hash."""
    provider_instance = mock_ionq_provider
    provider_instance._hash = 1234
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    assert result == 1234

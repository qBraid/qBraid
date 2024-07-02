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
Unit tests for OQCProvider class

"""
from unittest.mock import Mock, patch

import numpy as np
import openqasm3
import pytest

from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
from qbraid.runtime import DeviceType, TargetProfile
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.ionq import IonQDevice, IonQJob, IonQJobResult, IonQProvider, IonQSession
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
        "qubits": 30,
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
    with patch("qbraid_core.sessions.Session") as mock_session:
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
            assert test_device.profile["device_type"] == DeviceType.QPU.name
            assert test_device.profile["num_qubits"] in [device["qubits"] for device in DEVICE_DATA]
            assert test_device.profile["program_spec"] == ProgramSpec(openqasm3.ast.Program)

        test_device = provider.get_device("qpu.harmony")
        assert isinstance(test_device, IonQDevice)
        assert test_device.profile["device_id"] == "qpu.harmony"
        assert test_device.profile["device_type"] == DeviceType.QPU.name
        assert test_device.profile["num_qubits"] == 11
        assert test_device.profile["program_spec"] == ProgramSpec(openqasm3.ast.Program)
        assert test_device.profile["basis_gates"] == set(SUPPORTED_GATES)


def test_ionq_provider_device_unavailable():
    """Test getting IonQ provider and different status devices."""

    class MockSession:
        """Mock session class."""

        def get_device(self, device_id: str):
            """Mock get_device method."""
            res = DEVICE_DATA[0]
            match device_id:
                case "qpu.harmony":
                    res["status"] = "unavailable"
                case "qpu.aria-1":
                    res["status"] = "offline"
                case "qpu.aria-2":
                    res["status"] = "available"
                case "fake_device":
                    res["status"] = "fake_status"
            return res

    unavailable_profile = TargetProfile("qpu.harmony", DeviceType.QPU)
    unavailable_device = IonQDevice(unavailable_profile, MockSession())
    assert unavailable_device.status() == DeviceStatus.UNAVAILABLE

    offline_profile = TargetProfile("qpu.aria-1", DeviceType.QPU)
    offline_device = IonQDevice(offline_profile, MockSession())
    assert offline_device.status() == DeviceStatus.OFFLINE

    available_profile = TargetProfile("qpu.aria-2", DeviceType.QPU)
    available_device = IonQDevice(available_profile, MockSession())
    assert available_device.status() == DeviceStatus.ONLINE

    fake_profile = TargetProfile("fake_device", DeviceType.QPU)
    fake_device = IonQDevice(fake_profile, MockSession())
    with pytest.raises(ValueError):
        fake_device.status()


def test_ionq_device_extract_gate_data():
    """Test extracting gate data from a OpenQASM 3 program."""
    qasm3_str = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
x q[0];
not q[1];
y q[0];
z q[0];
rx(pi / 4) q[0];
ry(pi / 2) q[0];
rz(3 * pi / 4) q[0];
h q[0];
cx q[0], q[1];
CX q[1], q[2];
cnot q[2], q[0];
ccx q[0], q[1], q[2];
toffoli q[2], q[1], q[0];
s q[0];
sdg q[0];
si q[0];
t q[0];
tdg q[0];
ti q[1];
sx q[0];
v q[1];
sxdg q[0];
vi q[1];
swap q[0], q[1];
"""
    expected = [
        {"gate": "x", "target": 0},
        {"gate": "not", "target": 1},
        {"gate": "y", "target": 0},
        {"gate": "z", "target": 0},
        {"gate": "rx", "target": 0, "rotation": 0.7853981633974483},
        {"gate": "ry", "target": 0, "rotation": 1.5707963267948966},
        {"gate": "rz", "target": 0, "rotation": 2.356194490192345},
        {"gate": "h", "target": 0},
        {"gate": "cnot", "control": 0, "target": 1},
        {"gate": "cnot", "control": 1, "target": 2},
        {"gate": "cnot", "control": 2, "target": 0},
        {"gate": "cnot", "controls": [0, 1], "target": 2},
        {"gate": "cnot", "controls": [2, 1], "target": 0},
        {"gate": "s", "target": 0},
        {"gate": "si", "target": 0},
        {"gate": "si", "target": 0},
        {"gate": "t", "target": 0},
        {"gate": "ti", "target": 0},
        {"gate": "ti", "target": 1},
        {"gate": "v", "target": 0},
        {"gate": "v", "target": 1},
        {"gate": "vi", "target": 0},
        {"gate": "vi", "target": 1},
        {"gate": "swap", "targets": [0, 1]},
    ]
    qasm3_program = openqasm3.parser.parse(qasm3_str)
    actual = IonQDevice.extract_gate_data(qasm3_program)

    assert actual == expected


def test_ionq_device_transform_run_input():
    """Test transforming OpenQASM 3 string to supported gates + json format."""
    qasm_input = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
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
    assert isinstance(res, IonQJobResult)
    np.testing.assert_array_equal(res.measurements(), np.array([[0, 0], [0, 1]]))


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

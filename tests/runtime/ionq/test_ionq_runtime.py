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
import uuid
from itertools import combinations
from typing import Any, Optional
from unittest.mock import Mock, patch

import pytest

from qbraid.passes.qasm import normalize_qasm_gate_params, rebase
from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
from qbraid.programs.gate_model.ionq import IONQ_NATIVE_GATES_BASE, IONQ_QIS_GATES
from qbraid.runtime import GateModelResultData, ResourceNotFoundError, Result, TargetProfile
from qbraid.runtime.enums import DeviceStatus, JobStatus
from qbraid.runtime.ionq import IonQDevice, IonQJob, IonQProvider, IonQSession
from qbraid.runtime.ionq.job import IonQJobError

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

CHARACTERIZATION_DATA = {
    "connectivity": list(combinations(range(11), 2)),
    "qubits": 11,
    "fidelity": {"1q": {"mean": 0.9973}, "spam": {"mean": 0.993}, "2q": {"mean": 0.9002}},
    "timing": {
        "1q": 1e-05,
        "reset": 2e-05,
        "t1": 10000,
        "readout": 0.00013,
        "t2": 0.2,
        "2q": 0.0002,
    },
    "date": 1725102011,
    "id": "f518d0c9-34c6-4854-890e-a0e4f339bd64",
    "backend": "qpu.harmony",
}


def mock_characterization(device_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Mock get characterization method."""
    if device_data["backend"] == CHARACTERIZATION_DATA["backend"]:
        return CHARACTERIZATION_DATA.copy()
    return None


@pytest.fixture
def program_spec():
    """Return a ProgramSpec instance for IonQ."""
    return [ProgramSpec(str, alias="qasm2"), ProgramSpec(str, alias="qasm3")]


def test_ionq_provider_get_device(program_spec):
    """Test getting IonQ provider and device."""
    with (
        patch("qbraid.runtime.ionq.provider.Session") as mock_session,
        patch(
            "qbraid.runtime.ionq.provider.IonQProvider._get_characterization"
        ) as mock_get_characterization,
    ):

        mock_get_characterization.side_effect = mock_characterization
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
            assert test_device.profile["program_spec"] == program_spec

        test_device = provider.get_device("qpu.harmony")
        assert isinstance(test_device, IonQDevice)
        assert test_device.profile["device_id"] == "qpu.harmony"
        assert test_device.profile["simulator"] is False
        assert test_device.profile["num_qubits"] == 11
        assert test_device.profile["program_spec"] == program_spec
        assert test_device.profile["basis_gates"] == set(IONQ_QIS_GATES + IONQ_NATIVE_GATES_BASE)
        assert test_device.profile["characterization"] == CHARACTERIZATION_DATA


def test_get_device_characterization_from_data():
    """Test getting fetching device characterization from characterization url in device data."""
    with patch("qbraid.runtime.ionq.provider.IonQSession") as mock_session:
        mock_session.return_value.get.return_value.json.return_value = CHARACTERIZATION_DATA

        provider = IonQProvider(api_key="fake_api_key")
        harmony_data = DEVICE_DATA[0]
        characterization = provider._get_characterization(harmony_data)
        assert characterization == CHARACTERIZATION_DATA


def test_provider_session_device_not_found_error():
    """Test that a ValueError is raised if the device is not found."""
    with patch("qbraid.runtime.ionq.provider.Session") as mock_session:
        mock_session.return_value.get.return_value.json.return_value = DEVICE_DATA

        provider = IonQProvider(api_key="fake_api_key")

        with pytest.raises(ResourceNotFoundError, match="Device 'fake_device' not found."):
            provider.get_device("fake_device")


def test_ionq_provider_device_unavailable():
    """Test getting IonQ provider and different status devices."""

    class MockSession:
        """Mock session class."""

        def get_device(self, device_id: str):
            """Mock get_device method."""
            res = DEVICE_DATA[0]
            if device_id == "qpu.harmony":
                res["status"] = "retired"
            elif device_id == "qpu.aria-1":
                res["status"] = "offline"
            elif device_id == "qpu.aria-2":
                res["status"] = "available"
            elif device_id == "simulator":
                res["status"] = "available"
            elif device_id == "qpu.forte-1":
                res["status"] = "unavailable"
            elif device_id == "fake_device":
                res["status"] = "fake_status"
            return res

    unavailable_profile = TargetProfile(device_id="qpu.forte-1", simulator=False)
    unavailable_device = IonQDevice(unavailable_profile, MockSession())
    assert unavailable_device.status() == DeviceStatus.UNAVAILABLE

    offline_profile = TargetProfile(device_id="qpu.aria-1", simulator=False)
    offline_device = IonQDevice(offline_profile, MockSession())
    assert offline_device.status() == DeviceStatus.OFFLINE

    available_profile = TargetProfile(device_id="qpu.aria-2", simulator=False)
    available_device = IonQDevice(available_profile, MockSession())
    assert available_device.status() == DeviceStatus.ONLINE

    retired_profile = TargetProfile(device_id="qpu.harmony", simulator=False)
    retired_device = IonQDevice(retired_profile, MockSession())
    assert retired_device.status() == DeviceStatus.RETIRED

    fake_profile = TargetProfile(device_id="fake_device", simulator=False)
    fake_device = IonQDevice(fake_profile, MockSession())
    with pytest.raises(ValueError):
        fake_device.status()


@pytest.fixture
def qis_input_decomp():
    """Return a QIS gateset input."""
    return {
        "format": "ionq.circuit.v0",
        "gateset": "qis",
        "qubits": 2,
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "h", "target": 1},
            {"gate": "ry", "target": 1, "rotation": 0.39269908169872414},
            {"gate": "cnot", "control": 0, "target": 1},
            {"gate": "ry", "target": 1, "rotation": -0.39269908169872414},
            {"gate": "cnot", "control": 0, "target": 1},
        ],
    }


@pytest.fixture
def qis_input():
    """Return a QIS gateset input."""
    return {
        "format": "ionq.circuit.v0",
        "gateset": "qis",
        "qubits": 2,
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "h", "target": 1},
            {"gate": "ry", "control": 0, "target": 1, "rotation": 0.7853981633974483},
        ],
    }


@pytest.fixture
def native_input():
    """Return a native gateset input."""
    return {
        "format": "ionq.circuit.v0",
        "gateset": "native",
        "qubits": 3,
        "circuit": [
            {"gate": "ms", "targets": [0, 1], "phases": [0, 0]},
            {"gate": "ms", "targets": [1, 2], "phases": [-0.5, 0.6], "angle": 0.1},
            {"gate": "gpi", "phase": 0, "target": 0},
            {"gate": "gpi2", "phase": 0.2, "target": 1},
        ],
    }


def test_ionq_device_transform_run_input(qis_input, qis_input_decomp):
    """Test transforming OpenQASM 2 string to supported gates + json format."""
    qasm_input = """
    OPENQASM 2.0;
    qreg q[2];
    h q[0];
    h q[1];
    cry(pi/4) q[0], q[1];
    """

    with (
        patch("qbraid.runtime.ionq.provider.Session") as mock_session,
        patch(
            "qbraid.runtime.ionq.provider.IonQProvider._get_characterization"
        ) as mock_get_characterization,
    ):

        mock_get_characterization.side_effect = mock_characterization
        mock_session.return_value.get.return_value.json.return_value = DEVICE_DATA

        provider = IonQProvider(api_key="fake_api_key")
        test_devices = provider.get_devices()
        device = test_devices[0]
        qasm_compat = device.transform(qasm_input)
        program_json = device.to_ir(qasm_compat)
        assert program_json == qis_input

        qasm_rebased = rebase(qasm_input, gateset={"h", "ry", "cx"}, gate_mappings={"cx": "cnot"})
        qasm_decomp = normalize_qasm_gate_params(qasm_rebased)
        program_json_decomp = device.to_ir(qasm_decomp)
        assert program_json_decomp == qis_input_decomp

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

    def _validate_metadata(metadata):
        assert isinstance(metadata, dict)
        assert metadata["job_id"] == "c86a043a-6aea-47cf-b3a6-70ab1e538cab"
        assert metadata["shots"] == 2
        assert metadata["status"] == JobStatus.COMPLETED

    job_metadata = job.metadata()
    _validate_metadata(job_metadata)

    # test caching
    job_metadata = job.metadata()
    _validate_metadata(job_metadata)

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


def test_ionq_average_queue_time():
    """Test getting the average queue time of an IonQDevice."""
    device = IonQDevice(
        TargetProfile(device_id="simulator", simulator=False),
        IonQSession("fake_api_key"),
    )
    with patch("qbraid_core.sessions.Session.get") as mock_get:
        mock_get.return_value.json.return_value = DEVICE_DATA

        assert device.avg_queue_time() == 0


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
    with patch("qbraid_core.sessions.Session.get") as mock_get:
        mock_get.return_value.json.return_value = DEVICE_DATA
        with patch("qbraid_core.sessions.Session.post") as mock_post:
            mock_post.return_value.json.return_value = {"error": "fake_error"}

            with pytest.raises(ValueError):
                device.run(circuit, shots=2)


def test_ionq_device_str_representation():
    """Test the string representation of an IonQDevice."""
    profile = TargetProfile(device_id="simulator", simulator=True)
    session = IonQSession("fake_api_key")
    device = IonQDevice(profile, session)
    assert str(device) == "IonQDevice('simulator')"


@pytest.mark.parametrize("result", [{"probabilities": {"0": 0.5, "1": 0.5}}, {"shots": 100}])
def test_get_counts_raises_value_error_for_missing_data(result):
    """Test that _get_counts raises a ValueError if shots or probabilities are missing."""
    with pytest.raises(ValueError) as excinfo:
        IonQJob._get_counts(result)
    assert "Missing shots or probabilities in result data." in str(excinfo.value)


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


def test_ionq_session_raises_for_no_api_key(monkeypatch):
    """Test that IonQSession raises an error if no API key is provided."""
    monkeypatch.setenv("IONQ_API_KEY", "")

    with pytest.raises(ValueError) as excinfo:
        IonQSession()
    assert "An IonQ API key is required to initialize the session." in str(excinfo.value)


def test_ionq_session_api_key_from_env_var(monkeypatch):
    """Test that IonQSession gets the API key from the IONQ_API_KEY environment variable."""
    api_key = uuid.uuid4().hex
    monkeypatch.setenv("IONQ_API_KEY", api_key)

    session = IonQSession()

    assert session.api_key == api_key


def test_squash_multicircuit_input_empty_batch():
    """Test with an empty batch_input to ensure ValueError is raised."""
    with pytest.raises(ValueError, match="run_input list cannot be empty."):
        IonQDevice._squash_multicircuit_input([])


def test_squash_multicircuit_input_inconsistent_format(native_input):
    """Test with inconsistent formats to ensure ValueError is raised."""
    batch_input = [
        native_input,
        {**native_input, "format": "ionq.circuit.v1"},
    ]
    with pytest.raises(
        ValueError, match="All run_inputs must have the same value for key 'format'."
    ):
        IonQDevice._squash_multicircuit_input(batch_input)


def test_squash_multicircuit_input_inconsistent_gateset(qis_input, native_input):
    """Test with inconsistent basis_gatess to ensure ValueError is raised."""
    batch_input = [
        qis_input,
        native_input,
    ]
    with pytest.raises(
        ValueError, match="All run_inputs must have the same value for key 'gateset'."
    ):
        IonQDevice._squash_multicircuit_input(batch_input)


def test_squash_multicircuit_input_missing_required_field(native_input):
    """Test with missing required fields to ensure ValueError is raised."""
    batch_input = [
        {**native_input, "qubits": None},
        native_input,
    ]
    with pytest.raises(ValueError, match="All run_inputs must be an instance of ~IonQDict."):
        IonQDevice._squash_multicircuit_input(batch_input)


def test_squash_multicircuit_input_valid_single_entry(native_input):
    """Test with a valid single entry in batch_input."""
    batch_input = [native_input]
    result = IonQDevice._squash_multicircuit_input(batch_input)
    assert result == {
        "format": native_input["format"],
        "gateset": native_input["gateset"],
        "qubits": native_input["qubits"],
        "circuits": [{"circuit": native_input["circuit"], "name": "Circuit 0"}],
    }


def test_squash_multicircuit_input_valid_multiple_entries(native_input):
    """Test with multiple valid entries in batch_input."""
    modified_native_input = {**native_input, "qubits": 5, "circuit": native_input["circuit"]}
    batch_input = [native_input, modified_native_input]

    result = IonQDevice._squash_multicircuit_input(batch_input)
    assert result == {
        "format": native_input["format"],
        "gateset": native_input["gateset"],
        "qubits": 5,
        "circuits": [
            {"circuit": native_input["circuit"], "name": "Circuit 0"},
            {"circuit": modified_native_input["circuit"], "name": "Circuit 1"},
        ],
    }


def random_ionq_id(user=False):
    """Return a random IonQ ID."""
    hex = uuid.uuid4().hex

    if user:
        return hex[:24]

    return f"{hex[:8]}-{hex[8:12]}-{hex[12:16]}-{hex[16:20]}-{hex[20:]}"


def generate_job_data_ids(num_children=0):
    """Generate random IonQ job data IDs."""
    return {
        "id": random_ionq_id(),
        "submitted_by": random_ionq_id(user=True),
        "project_id": random_ionq_id(),
        "children": [random_ionq_id() for _ in range(num_children)],
    }


@pytest.fixture
def multicircuit_job_data():
    """Return mock data for a multicircuit job."""
    ids = generate_job_data_ids(num_children=2)

    return {
        **ids,
        "status": "completed",
        "target": "simulator",
        "type": "circuit",
        "qubits": 2,
        "circuits": 2,
        "results_url": f"/v0.3/jobs/{ids['id']}/results",
        "gate_counts": {"1q": 2, "2q": 2},
        "cost_usd": 0,
        "request": 1731088388,
        "start": 1731088390,
        "response": 1731088390,
        "execution_time": 98,
        "predicted_execution_time": 8,
        "noise": {"model": "ideal"},
        "error_mitigation": {"debias": False},
        "probabilities": {
            ids["children"][0]: {"0": 0.65, "3": 0.35},
            ids["children"][1]: {"0": 0.5, "3": 0.5},
        },
        "shots": 1000,
    }


def test_ionq_get_counts_multicircuit_job(multicircuit_job_data):
    """Test getting counts for a multi-circuit job."""
    counts = IonQJob._get_counts(multicircuit_job_data)
    assert counts == [
        {"00": 650, "11": 350},
        {"00": 500, "11": 500},
    ]

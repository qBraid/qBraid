# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name,unused-argument

"""
Unit tests for OQCProvider class

"""
from __future__ import annotations

import datetime
import json
import logging
import os
import textwrap
import uuid
from typing import Optional, Union
from unittest.mock import MagicMock, Mock, patch

import pytest
from requests import ReadTimeout

from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import ResourceNotFoundError

try:
    from qcaas_client.client import OQCClient, QPUTask, QPUTaskErrors, QPUTaskResult  # type: ignore

    from qbraid.programs import NATIVE_REGISTRY, ExperimentType, ProgramSpec
    from qbraid.runtime import GateModelResultData, Result, TargetProfile
    from qbraid.runtime.enums import DeviceStatus, JobStatus
    from qbraid.runtime.exceptions import ResourceNotFoundError
    from qbraid.runtime.oqc import OQCDevice, OQCJob, OQCProvider
    from qbraid.runtime.postprocess import counts_to_probabilities
    from qbraid.runtime.schemas.base import USD

    FIXTURE_COUNT = sum(key in NATIVE_REGISTRY for key in ["qiskit", "braket", "cirq"])

    oqc_extras_installed = True
except ImportError as err:
    FIXTURE_COUNT = 0

    oqc_extras_installed = False

    logging.warning("OQC runtime tests will be skipped: %s", err)

pytestmark = pytest.mark.skipif(oqc_extras_installed is False, reason="qcaas_client not installed")

LUCY_SIM_ID = "qpu:uk:2:d865b5a184"
TOSHIKO_ID = "qpu:jp:3:673b1ad43c"

LUCY_FEATURE_SET = {"always_on": True, "qubit_count": 8, "simulator": True}
TOSHIKO_FEATURE_SET = {
    "qubit_count": 32,
    "Maximum Shots": 100000,
    "Maximum Repetition Period": "1 second",
    "Maximum Shots x Repetition Period": "600 seconds",
}

LUCY_SIM_MOCK_DATA = {
    "active": True,
    "feature_set": json.dumps(LUCY_FEATURE_SET),
    "generation": 2,
    "id": LUCY_SIM_ID,
    "name": "Lucy Simulator",
    "price_per_shot": "0",
    "price_per_task": "0",
    "region": "uk",
    "status": "ACTIVE",
    "url": "https://uk.cloud.oqc.app/d865b5a184",
}

TOSHIKO_MOCK_DATA = {
    "active": True,
    "feature_set": json.dumps(TOSHIKO_FEATURE_SET),
    "generation": 3,
    "id": TOSHIKO_ID,
    "name": "OQC Toshiko Tokyo-1",
    "price_per_shot": "0.0013",
    "price_per_task": "0",
    "region": "jp",
    "status": "ACTIVE",
    "url": "https://jp.cloud.oqc.app/673b1ad43c",
}

MOCK_TIMINGS = {
    "RECEIVER_DEQUEUED": "2023-10-17 11:24:32.937188+00:00",
    "RECEIVER_ENQUEUED": "2023-10-17 11:24:32.996594+00:00",
    "RECEIVER_FROM_SCC": "2023-10-17 11:24:32.996594+00:00",
    "RECEIVER_TO_SCC": "2023-10-17 11:24:32.938188+00:00",
    "SERVER_DEQUEUED": "2023-10-17 11:24:36.057355+00:00",
    "SERVER_ENQUEUED": "2023-10-17 11:24:35.946476+00:00",
    "SERVER_RECEIVED": "2023-10-17 11:24:35.904885+00:00",
}

MOCK_METRICS = {"optimized_circuit": "dummy", "optimized_instruction_count": 42}

MOCK_TASK_ID = "e35fb436-ff08-44c8-8acc-7d5a1f1a0ada"
MOCK_TASK_ID_NO_RESULT = "e35fb436-ff08-44c8-8acc-7d5a1f1a0adb"

MOCK_TASK_METADATA = {
    "allow_support_access": False,
    "config": '{"$type": "<class \'scc.compiler.config.CompilerConfig\'>", "$data": {"repeats": null, "repetition_period": null, "results_format": {"$type": "<class \'scc.compiler.config.QuantumResultsFormat\'>", "$data": {"format": null, "transforms": {"$type": "<enum \'scc.compiler.config.ResultsFormatting\'>", "$value": 2}}}, "metrics": {"$type": "<enum \'scc.compiler.config.MetricsType\'>", "$value": 6}, "active_calibrations": [], "optimizations": null, "error_mitigation": null}}',  # pylint: disable=line-too-long
    "created_at": "Wed, 12 Jun 2024 20:11:15 GMT",
    "id": MOCK_TASK_ID,
    "qpu_id": LUCY_SIM_ID,
    "tag": None,
}

MOCK_RESULT = {"c": {"00": 52, "11": 48}}

NOW = datetime.datetime.now()
NEXT_YEAR = NOW.year + 1

TOSHIKO_EXEC_ESTIMATE = {
    "qpu_wait_times": [
        {
            "average_processing_seconds": 0.0,
            "estimated_availability_time": f"{NEXT_YEAR}-11-18 00:50:00",
            "qpu_id": "qpu:jp:3:673b1ad43c",
            "tasks_in_queue": 21,
            "timestamp": f"{NOW.year}-11-13 16:20:43.229464",
            "windows": [
                {
                    "end_time": f"{NEXT_YEAR}-11-18 04:00:00",
                    "start_time": f"{NEXT_YEAR}-11-18 00:50:00",
                    "window_description": "NEXT",
                },
                {
                    "end_time": f"{NEXT_YEAR}-11-18 13:00:00",
                    "start_time": f"{NEXT_YEAR}-11-18 09:50:00",
                    "window_description": "FUTURE",
                },
                {
                    "end_time": f"{NEXT_YEAR}-11-19 04:00:00",
                    "start_time": f"{NEXT_YEAR}-11-19 00:50:00",
                    "window_description": "FUTURE",
                },
                {
                    "end_time": f"{NEXT_YEAR}-11-19 13:00:00",
                    "start_time": f"{NEXT_YEAR}-11-19 09:50:00",
                    "window_description": "FUTURE",
                },
            ],
        }
    ]
}


def online_window() -> str:
    """Return a window start time for an online QPU."""
    now = datetime.datetime.now()
    start_time = f"{now.year}-{now.month}-{now.day} {(now.hour):02}:00:00"
    end_time = f"{now.year}-{now.month}-{now.day} {(now.hour):02}:59:59"
    return start_time, end_time


@pytest.fixture
def program():
    """Return a QASM3 program."""
    qasm3 = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    bit[2] c;

    h q[0];
    cx q[0], q[1];

    c = measure q;
    """

    qasm3_compat = textwrap.dedent(qasm3).strip()
    return qasm3_compat


@pytest.fixture
def optimized_program():
    """Return a QASM3 program."""
    qasm3 = """
    OPENQASM 3.0;
    qubit[2] q;
    bit[2] c;
    h q[0];
    cx q[0], q[1];
    c = measure q;
    """
    qasm3_compat = textwrap.dedent(qasm3).strip()
    return qasm3_compat


class MockOQCClient:
    """Test class for OQC client."""

    def __init__(self, authentication_token=None, **kwargs):
        self._authentication_token = authentication_token
        self.default_qpu_id = "qpu:uk:3:9829a5504f"
        self.url = "https://cloud.oqc.app/"
        self._toshiko_online = False

    def get_qpus(self):
        """Get QPUs."""
        return [LUCY_SIM_MOCK_DATA.copy(), TOSHIKO_MOCK_DATA.copy()]

    def schedule_tasks(
        self,
        tasks: Union[QPUTask, list[QPUTask]],
        qpu_id: Optional[str] = None,
        tag: Optional[str] = None,
    ):
        """Schedule tasks for the QPU."""
        if not isinstance(tasks, list):
            tasks = [tasks]

        first_qpu_id = None
        assigned_mock_task_id = False

        for task in tasks:
            if not isinstance(task, QPUTask):
                raise ValueError("All tasks must be of type QPUTask")

            if qpu_id:
                task.qpu_id = qpu_id
            else:
                if not task.qpu_id:
                    task.qpu_id = self.default_qpu_id

                if first_qpu_id is None:
                    first_qpu_id = task.qpu_id
                elif task.qpu_id != first_qpu_id:
                    raise ValueError("All tasks must have the same qpu_id")

            if not task.task_id:
                if not assigned_mock_task_id:
                    task.task_id = MOCK_TASK_ID
                    assigned_mock_task_id = True
                else:
                    task.task_id = str(uuid.uuid4())

        return tasks

    def get_next_window(self, qpu_id: Optional[str] = None):
        """Get next window."""
        if qpu_id == LUCY_SIM_ID:
            start_time, _ = online_window()
            return start_time
        raise ReadTimeout

    def get_qpu_execution_estimates(self, qpu_ids: Optional[str] = None):
        """Get QPU execution estimates."""
        if qpu_ids == TOSHIKO_ID:
            exec_est = TOSHIKO_EXEC_ESTIMATE.copy()
            if self._toshiko_online:
                start_time, end_time = online_window()
                current_window = {
                    "end_time": end_time,
                    "start_time": start_time,
                    "window_description": "CURRENT",
                }
                new_windows = [current_window] + exec_est["qpu_wait_times"][0]["windows"]
                exec_est["qpu_wait_times"][0]["windows"] = new_windows
            return exec_est
        raise Exception("QPU execution estimates not available")

    def get_task_status(self, task_id: str, qpu_id: Optional[str] = None):
        """Get task status."""
        if task_id == MOCK_TASK_ID:
            return "COMPLETED"
        return "FAILED"

    def get_task_timings(self, task_id: str, qpu_id: Optional[str] = None):
        """Get task timings."""
        return MOCK_TIMINGS

    def get_task_metrics(self, task_id: str, qpu_id: Optional[str] = None):
        """Get task metrics."""
        return MOCK_METRICS

    def get_task_metadata(self, task_id: str, qpu_id: Optional[str] = None):
        """Get task metadata."""
        metadata = MOCK_TASK_METADATA.copy()
        metadata["id"] = task_id
        if qpu_id:
            metadata["qpu_id"] = qpu_id
        return metadata

    def get_task_errors(self, task_id: str, qpu_id: Optional[str] = None):
        """Get task errors."""
        if task_id == MOCK_TASK_ID:
            return None
        return QPUTaskErrors("Error", 400)

    def get_task_results(self, task_id: str, qpu_id: Optional[str] = None):
        """Get task results."""
        qpu_id_matches = qpu_id is None or qpu_id == LUCY_SIM_ID
        result = MOCK_RESULT if task_id == MOCK_TASK_ID and qpu_id_matches else None
        metrics = self.get_task_metrics(task_id, qpu_id)
        error_details = self.get_task_errors(task_id, qpu_id)
        return QPUTaskResult(task_id, result=result, metrics=metrics, error_details=error_details)

    def cancel_task(self, task_id: str, qpu_id: Optional[str] = None):
        """Cancel task."""
        return None


@pytest.fixture
def lucy_sim_id():
    """Return Lucy Simulator ID."""
    return LUCY_SIM_ID


@pytest.fixture
def toshiko_id():
    """Return Toshiko ID."""
    return TOSHIKO_ID


@pytest.fixture
def lucy_sim_data():
    """Return data for Lucy Simulator."""
    return LUCY_SIM_MOCK_DATA.copy()


@pytest.fixture
def toshiko_data():
    """Return data for Toshiko QPU."""
    return TOSHIKO_MOCK_DATA.copy()


@pytest.fixture
def mock_job_id():
    """Return a mock task ID."""
    return MOCK_TASK_ID


@pytest.fixture
def oqc_client():
    """Return a fake OQC client."""
    return MockOQCClient("fake_token")


@pytest.fixture
def target_profile(lucy_sim_data):
    """Return a target profile for Lucy Simulator."""
    feature_set = LUCY_FEATURE_SET.copy()
    simulator = feature_set.pop("simulator")
    num_qubits = feature_set.pop("qubit_count")

    return TargetProfile(
        device_id=lucy_sim_data["id"],
        device_name=lucy_sim_data["name"],
        simulator=simulator,
        experiment_type=ExperimentType.GATE_MODEL,
        endpoint_url=lucy_sim_data["url"],
        num_qubits=num_qubits,
        program_spec=ProgramSpec(str, alias="qasm3"),
        feature_set=feature_set,
        price_per_shot=USD(lucy_sim_data["price_per_shot"]),
        price_per_task=USD(lucy_sim_data["price_per_task"]),
        generation=lucy_sim_data["generation"],
        region=lucy_sim_data["region"],
    )


@pytest.fixture
def oqc_device(oqc_client, target_profile):
    """Return a fake OQC device."""
    return OQCDevice(profile=target_profile, client=oqc_client)


@pytest.fixture
def oqc_job(mock_job_id, oqc_client, oqc_device):
    """Return a fake OQC job."""
    return OQCJob(mock_job_id, client=oqc_client, device=oqc_device)


@pytest.fixture
def oqc_job_failed(oqc_client, oqc_device):
    """Return a fake OQC job that failed."""
    return OQCJob("failed_job_id", client=oqc_client, device=oqc_device)


def test_oqc_device_str_representation(oqc_device):
    """Test the string representation of an OQC device."""
    assert str(oqc_device) == "OQCDevice('Lucy Simulator')"


def test_oqc_provider_get_devices(lucy_sim_data, toshiko_data):
    """Test getting all OQC devices."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]
        provider = OQCProvider(token="fake_token")
        assert isinstance(provider, OQCProvider)
        assert isinstance(provider.client, OQCClient)
        assert provider.client == mock_client.return_value
        devices = provider.get_devices()
        assert isinstance(devices, list)
        assert {device.id for device in devices} == {lucy_sim_data["id"], toshiko_data["id"]}


def test_oqc_provider_get_device_profile(lucy_sim_data, toshiko_data):
    """Test getting a specific OQC device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]
        provider = OQCProvider(token="fake_token")
        test_device = provider.get_device(lucy_sim_data["id"])
        assert isinstance(test_device.status(), DeviceStatus)
        assert isinstance(test_device, OQCDevice)
        assert test_device.profile["device_id"] == lucy_sim_data["id"]
        assert test_device.profile["price_per_shot"] == USD(lucy_sim_data["price_per_shot"])
        assert test_device.profile["price_per_task"] == USD(lucy_sim_data["price_per_task"])
        assert isinstance(test_device.client, OQCClient)


def test_oqc_provider_get_device_status_offline(lucy_sim_data, toshiko_data):
    """Test getting a specific OQC device."""
    toshiko_data["active"] = False
    toshiko_data["status"] = "INACTIVE"
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]
        provider = OQCProvider(token="fake_token")
        test_device = provider.get_device(toshiko_data["id"])
        assert test_device.status() == DeviceStatus.OFFLINE


def test_oqc_device_status_from_window_unavailable(lucy_sim_data, toshiko_data):
    """Test that device status value varies correctly based on next available window."""
    lucy_sim_data["feature_set"] = json.dumps(
        {"always_on": False, "qubit_count": 8, "simulator": True}
    )
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]
        provider = OQCProvider(token="fake_token")

        now = datetime.datetime.now()
        year, month, day = now.year, now.month, now.day
        window = f"{year + 1}-{month}-{day} 00:50:00"
        mock_client.return_value.get_next_window.return_value = window
        unavailable_device = provider.get_device(lucy_sim_data["id"])
        assert unavailable_device.status() == DeviceStatus.UNAVAILABLE


def test_oqc_device_status_always_on(lucy_sim_data, toshiko_data):
    """Test that device status is ONLINE for devices that are always on."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]
        provider = OQCProvider(token="fake_token")
        device = provider.get_device(lucy_sim_data["id"])
        assert device.status() == DeviceStatus.ONLINE
        mock_client.get_next_window.assert_not_called()


def test_get_next_window_read_timeout(toshiko_id):
    """Test getting the next window with a timeout results in status unavialable."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = MockOQCClient()
        provider = OQCProvider(token="fake_token")
        device = provider.get_device(toshiko_id)
        assert device.status() == DeviceStatus.UNAVAILABLE


def test_oqc_device_status_from_qpu_exec_est_unavailable(lucy_sim_data, toshiko_data):
    """Test that device status value varies correctly based on next available window."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]

        provider = OQCProvider(token="fake_token")
        qpu_device = provider.get_device(toshiko_data["id"])
        qpu_device._client = MockOQCClient(authentication_token="fake_token")
        assert qpu_device.status() == DeviceStatus.UNAVAILABLE


def test_oqc_device_status_from_qpu_exec_est_online(lucy_sim_data, toshiko_data):
    """Test that device status value varies correctly based on next available window."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]

        provider = OQCProvider(token="fake_token")
        qpu_device = provider.get_device(toshiko_data["id"])
        qpu_device._client = MockOQCClient(authentication_token="fake_token")
        qpu_device._client._toshiko_online = True
        assert qpu_device.status() == DeviceStatus.ONLINE
        assert qpu_device.queue_depth() == 21


def test_oqc_queue_depth_raises_for_simulator(lucy_sim_data, toshiko_data):
    """Test that the queue depth method raises an error for a simulator device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]

        provider = OQCProvider(token="fake_token")
        simulator_device = provider.get_device(lucy_sim_data["id"])
        with pytest.raises(ResourceNotFoundError) as excinfo:
            simulator_device.queue_depth()
        assert "Queue depth is not available for this device." in str(excinfo.value)


def test_oqc_provider_get_device_raises_not_found(lucy_sim_data, toshiko_data):
    """Test raising an error when a device is not found."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]
        provider = OQCProvider(token="fake_token")
        with pytest.raises(ResourceNotFoundError):
            provider.get_device("fake_id")


def test_oqc_device_status_raises(lucy_sim_data, toshiko_data):
    """Test OQC device status method raises an error for bad request data."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]

        provider = OQCProvider(token="fake_token")
        fake_profile = TargetProfile(
            device_id="fake_id",
            device_name="Fake Device",
            simulator=True,
            experiment_type=ExperimentType.GATE_MODEL,
            endpoint_url="https://uk.cloud.oqc.app/fake_id",
            num_qubits=8,
            program_spec=ProgramSpec(str, alias="qasm3"),
        )
        fake_device = OQCDevice(profile=fake_profile, client=provider.client)
        with pytest.raises(ResourceNotFoundError):
            fake_device.status()


@pytest.mark.parametrize(
    "data_modifications, expected_error_message",
    [
        ({"feature_set": ""}, "Failed to decode feature set data"),
        (
            {"feature_set": json.dumps({"simulator": True})},
            "Failed to gather profile data for device",
        ),
    ],
)
def test_oqc_provider_get_device_errors(lucy_sim_data, data_modifications, expected_error_message):
    """Test OQC provider get device method raises exceptions for various error conditions."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        invalid_lucy_sim_data = lucy_sim_data
        invalid_lucy_sim_data.update(data_modifications)
        mock_client.return_value.get_qpus.return_value = [invalid_lucy_sim_data]
        provider = OQCProvider(token="fake_token")

        with pytest.raises(ValueError) as excinfo:
            provider.get_device(lucy_sim_data["id"])
        assert expected_error_message in str(excinfo.value)


def test_build_runtime_profile(lucy_sim_data):
    """Test building a runtime profile for OQC device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        provider = OQCProvider(token="fake_token")
        profile = provider._build_profile(lucy_sim_data)
        assert isinstance(profile, TargetProfile)
        assert profile["device_id"] == lucy_sim_data["id"]
        assert profile["simulator"] is True
        assert profile["num_qubits"] == 8
        assert profile["program_spec"] == ProgramSpec(str, alias="qasm3")


@pytest.mark.parametrize("circuit", range(FIXTURE_COUNT), indirect=True)
def test_run_fake_job(circuit, oqc_device):
    """Test running a fake job."""
    job: OQCJob = oqc_device.run(circuit, shots=100)
    assert isinstance(job, OQCJob)
    assert isinstance(job.status(), JobStatus)
    assert isinstance(job.get_timings(), dict)
    assert isinstance(job.metrics(), dict)
    assert isinstance(job.metrics()["optimized_instruction_count"], int)
    assert isinstance(job.metadata(), dict)
    assert isinstance(job.get_errors(), (str, type(None)))

    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert result.data.get_counts() == MOCK_RESULT["c"]


def test_run_batch_fake_job(run_inputs, oqc_device):
    """Test running a batch of fake jobs."""
    job = oqc_device.run(run_inputs)
    assert isinstance(job, list)
    assert len(job) == len(run_inputs)
    assert all(isinstance(j, OQCJob) for j in job)


def test_cancel_job(oqc_device, program):
    """Test cancelling a fake job."""
    job = oqc_device.run(program, shots=100)
    assert isinstance(job, OQCJob)
    assert job.cancel() is None


@pytest.mark.remote
def test_oqc_runtime_remote_execution(program, optimized_program):
    """Test OQC runtime with remote execution."""
    token = os.getenv("OQC_AUTH_TOKEN")
    if token is None:
        pytest.skip("Missing OQC_AUTH_TOKEN")

    provider = OQCProvider(token=token)

    device = provider.get_device(LUCY_SIM_ID)
    assert isinstance(device, OQCDevice)
    assert device.status() == DeviceStatus.ONLINE

    shots = 100
    job = device.run(program, shots=shots)
    assert isinstance(job, OQCJob)

    job.wait_for_final_state()
    assert job.qpu_id == LUCY_SIM_ID
    assert job.is_terminal_state()
    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, Result)
    assert result.details["errors"] is None
    assert result.details["shots"] == shots

    optimized_out = result.details["metrics"]["optimized_circuit"]
    assert optimized_out.strip() == optimized_program.strip()

    data = result.data
    assert isinstance(data, GateModelResultData)

    counts = data.get_counts()
    assert len(counts) == 2
    assert set(counts.keys()) == {"00", "11"}
    assert sum(counts.values()) == shots
    assert data.measurements is None


def test_oqc_job_get_errors(oqc_job_failed):
    """Test getting errors from a failed job."""
    errors = oqc_job_failed.get_errors()
    assert errors == {"message": "Error", "code": 400}

    result = oqc_job_failed.result()
    assert result.success is False
    assert result.data.measurement_counts is None
    assert result.data.measurements is None


@patch("builtins.hash", autospec=True)
def test_hash_method_creates_and_returns_hash(mock_hash, oqc_client):
    """Test that the hash method creates and returns a hash."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        provider_instance = OQCProvider(token="fake_token")
        mock_hash.return_value = 9999
        provider_instance.client = oqc_client
        result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
        mock_hash.assert_called_once_with(("https://cloud.oqc.app/", "fake_token"))
        assert result == 9999
        assert provider_instance._hash == 9999


def test_hash_method_returns_existing_hash(oqc_client):
    """Test that the hash method returns an existing hash."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        provider_instance = OQCProvider(token="fake_token")
        provider_instance.client = oqc_client
        provider_instance._hash = 1234
        result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
        assert result == 1234


def test_job_result_method_raises_resource_not_found(oqc_job):
    """Test that the result method raises a ResourceNotFoundError when no result is found."""
    oqc_job._qpu_id = "mismatched_id"
    with pytest.raises(ResourceNotFoundError) as excinfo:
        oqc_job.result()
    assert "No result found for the task" in str(excinfo.value)


def test_job_get_counts_single_key():
    """Test that the _get_counts method returns the expected counts for a single key."""
    result = {"c": {"00": 1000, "01": 500}}
    expected = {"00": 1000, "01": 500}

    assert OQCJob._get_counts(result) == expected


@pytest.fixture
def multi_cbit_result_counts():
    """Return a result counts dictionary with multiple keys."""
    return {
        "c0": {"000000": 45, "111111": 55},
        "c1": {"000000": 45, "111111": 55},
        "c2": {"000000": 45, "111111": 55},
    }


def test_job_get_counts_multiple_keys(multi_cbit_result_counts):
    """Test that the _get_counts method returns the expected counts for multiple keys."""
    expected = [
        {"000000": 45, "111111": 55},
        {"000000": 45, "111111": 55},
        {"000000": 45, "111111": 55},
    ]

    assert OQCJob._get_counts(multi_cbit_result_counts) == expected


def test_job_get_counts_empty_dict():
    """Test that the _get_counts method raises a ValueError when the result dictionary is empty."""
    result = {}

    with pytest.raises(ValueError, match="The result dictionary must not be empty."):
        OQCJob._get_counts(result)


def test_job_get_counts_list_to_probabilities(multi_cbit_result_counts):
    """Test that the _get_counts method returns the expected probabilities for a list of counts."""
    expected = [
        {"000000": 0.45, "111111": 0.55},
        {"000000": 0.45, "111111": 0.55},
        {"000000": 0.45, "111111": 0.55},
    ]

    counts_list = OQCJob._get_counts(multi_cbit_result_counts)
    assert counts_to_probabilities(counts_list) == expected


def test_job_get_qpu_id_from_task_metadata(lucy_sim_id, oqc_job, oqc_client):
    """Test getting the qpu_id from the task metadata."""
    oqc_job._qpu_id = None
    oqc_job._device = None
    oqc_job._client = oqc_client
    assert oqc_job.qpu_id == lucy_sim_id

    oqc_job._qpu_id = None
    oqc_job._device = None
    oqc_client.get_task_metadata = MagicMock(return_value={"qpu_id": lucy_sim_id})
    oqc_job._client = oqc_client
    assert oqc_job.qpu_id == lucy_sim_id
    oqc_client.get_task_metadata.assert_called_once()


def test_oqc_provider_raises_for_no_token(monkeypatch):
    """Test that the OQCProvider raises an error when no token is provided."""
    monkeypatch.setenv("OQC_AUTH_TOKEN", "")

    with pytest.raises(ValueError) as excinfo:
        OQCProvider()
    assert "An OQC authenication token is required to initialize the provider." in str(
        excinfo.value
    )


@patch("qbraid.runtime.oqc.device.logger")
@patch("qbraid.runtime.oqc.device.OQCDevice.get_next_window")
def test_device_status_online(mock_get_next_window, mock_logger):
    mock_get_next_window.return_value = datetime.datetime(2023, 10, 31, 12, 0, 0)
    device = OQCDevice(profile=Mock(), client=Mock())
    result = device.status()
    assert result == DeviceStatus.ONLINE
    mock_logger.error.assert_not_called()


def test_build_compiler_config_unsupported_key():
    """Test that the build_compiler_config method raises an error for unsupported kwargs."""
    with pytest.raises(ValueError, match="Unsupported keyword argument"):
        OQCDevice._build_compiler_config(unsupported_kwarg="value")


def test_build_compiler_config_invalid_value():
    """Test that the build_compiler_config method raises an error for invalid values."""
    with pytest.raises(ValueError, match="Invalid configuration option"):
        OQCDevice._build_compiler_config(optimizations="invalid_value")


@patch("qbraid.runtime.oqc.device.logger")
def test_device_get_next_window_raises_resource_not_found(mock_logger, target_profile):
    """Test that the get_next_window method raises a ResourceNotFoundError when the window is not found."""
    client = Mock()
    client.get_next_window.side_effect = ReadTimeout
    client.get_qpu_execution_estimates.side_effect = Exception
    device = OQCDevice(target_profile, client)
    with pytest.raises(ResourceNotFoundError) as excinfo:
        device.get_next_window()
    assert "Falied to fetch next active window for device" in str(excinfo.value)
    mock_logger.error.assert_called_once()


@patch("qbraid.runtime.oqc.device.logger")
def test_catch_device_status_resource_not_found(mock_logger, lucy_sim_data, toshiko_data):
    """Test that device status is unavailable when get_next_window method raises error."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data, toshiko_data]

        provider = OQCProvider(token="fake_token")
        device = provider.get_device(toshiko_data["id"])

        with patch.object(device, "get_next_window", side_effect=ResourceNotFoundError):
            status = device.status()
            assert status == DeviceStatus.UNAVAILABLE
            mock_logger.info.assert_called_once()

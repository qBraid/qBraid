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
from unittest.mock import Mock, patch

import pytest

try:
    from qcaas_client.client import OQCClient, QPUTask, QPUTaskErrors, QPUTaskResult  # type: ignore

    from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
    from qbraid.runtime import GateModelResultData, Result, TargetProfile
    from qbraid.runtime.enums import DeviceStatus, ExperimentType, JobStatus
    from qbraid.runtime.exceptions import ResourceNotFoundError
    from qbraid.runtime.oqc import OQCDevice, OQCJob, OQCProvider

    FIXTURE_COUNT = sum(key in NATIVE_REGISTRY for key in ["qiskit", "braket", "cirq"])

    oqc_extras_installed = True
except ImportError as err:
    FIXTURE_COUNT = 0

    oqc_extras_installed = False

    logging.warning("OQC runtime tests will be skipped: %s", err)

pytestmark = pytest.mark.skipif(oqc_extras_installed is False, reason="qcaas_client not installed")

LUCY_SIM_ID = "qpu:uk:2:d865b5a184"

LUCY_FEATURE_SET = {"always_on": True, "qubit_count": 8, "simulator": True}

LUCY_SIM_MOCK_DATA = {
    "active": True,
    "feature_set": json.dumps(LUCY_FEATURE_SET),
    "generation": 2,
    "id": LUCY_SIM_ID,
    "name": "Lucy Simulator",
    "region": "uk",
    "url": "https://uk.cloud.oqc.app/d865b5a184",
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

MOCK_TASK_METADATA = {
    "allow_support_access": False,
    "config": '{"$type": "<class \'scc.compiler.config.CompilerConfig\'>", "$data": {"repeats": null, "repetition_period": null, "results_format": {"$type": "<class \'scc.compiler.config.QuantumResultsFormat\'>", "$data": {"format": null, "transforms": {"$type": "<enum \'scc.compiler.config.ResultsFormatting\'>", "$value": 2}}}, "metrics": {"$type": "<enum \'scc.compiler.config.MetricsType\'>", "$value": 6}, "active_calibrations": [], "optimizations": null, "error_mitigation": null}}',  # pylint: disable=line-too-long
    "created_at": "Wed, 12 Jun 2024 20:11:15 GMT",
    "id": MOCK_TASK_ID,
    "qpu_id": LUCY_SIM_ID,
    "tag": None,
}

MOCK_RESULT = {"c": {"00": 52, "11": 48}}


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


class MockOQCClient:
    """Test class for OQC client."""

    def __init__(self, authentication_token=None):
        self._authentication_token = authentication_token
        self.default_qpu_id = "qpu:uk:3:9829a5504f"

    def get_qpus(self):
        """Get QPUs."""
        return [LUCY_SIM_MOCK_DATA]

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
        return "2024-07-30 00:50:00"

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
        result = MOCK_RESULT if task_id == MOCK_TASK_ID else None
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
def lucy_sim_data():
    """Return data for Lucy Simulator."""
    return LUCY_SIM_MOCK_DATA


@pytest.fixture
def oqc_client():
    """Return a fake OQC client."""
    return MockOQCClient("fake_token")


@pytest.fixture
def target_profile(lucy_sim_data):
    """Return a target profile for Lucy Simulator."""
    return TargetProfile(
        device_id=lucy_sim_data["id"],
        device_name=lucy_sim_data["name"],
        simulator=LUCY_FEATURE_SET["simulator"],
        experiment_type=ExperimentType.GATE_MODEL,
        endpoint_url=lucy_sim_data["url"],
        num_qubits=LUCY_FEATURE_SET["qubit_count"],
        program_spec=ProgramSpec(str, alias="qasm2"),
    )


@pytest.fixture
def oqc_device(oqc_client, target_profile):
    """Return a fake OQC device."""
    return OQCDevice(profile=target_profile, client=oqc_client)


def test_oqc_provider_device(lucy_sim_id, lucy_sim_data):
    """Test OQC provider and device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_sim_data]
        provider = OQCProvider(token="fake_token")
        assert isinstance(provider, OQCProvider)
        assert isinstance(provider.client, OQCClient)
        assert provider.client == mock_client.return_value
        test_device = provider.get_device(lucy_sim_id)
        devices = provider.get_devices()
        assert isinstance(devices, list)
        assert any(device.id == test_device.id for device in devices)
        assert isinstance(test_device.status(), DeviceStatus)
        assert isinstance(test_device, OQCDevice)
        assert test_device.profile["device_id"] == lucy_sim_id
        with pytest.raises(ResourceNotFoundError):
            provider.get_device("fake_id")
        assert isinstance(test_device.client, OQCClient)
        lucy_sim_data["feature_set"] = json.dumps(
            {"always_on": False, "qubit_count": 8, "simulator": True}
        )
        now = datetime.datetime.now()
        year, month, day = now.year, now.month, now.day
        window = f"{year + 1}-{month}-{day} 00:50:00"
        mock_client.return_value.get_next_window.return_value = window
        unavailable_device = provider.get_device(lucy_sim_id)
        assert unavailable_device.status() == DeviceStatus.OFFLINE
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

        window = f"{year - 1}-{month}-{day} 00:50:00"
        mock_client.return_value.get_next_window.return_value = window
        always_on_false_available_device = provider.get_device(lucy_sim_id)
        assert always_on_false_available_device.status() == DeviceStatus.ONLINE


@pytest.mark.parametrize(
    "data_modifications, expected_error_message",
    [
        ({"feature_set": ""}, "Failed to decode feature set data for device"),
        (
            {"feature_set": json.dumps({"qubit_count": 8})},
            "Failed to gather profile data for device",
        ),
    ],
)
def test_oqc_provider_get_device_errors(lucy_sim_data, data_modifications, expected_error_message):
    """Test OQC provider get device method raises exceptions for various error conditions."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        invalid_lucy_sim_data = lucy_sim_data.copy()
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
def test_oqc_runtime_remote_execution(program):
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
    assert result.details["metrics"]["optimized_circuit"] == program

    data = result.data
    assert isinstance(data, GateModelResultData)

    counts = data.get_counts()
    assert len(counts) == 2
    assert set(counts.keys()) == {"00", "11"}
    assert sum(counts.values()) == shots
    assert data.measurements is None

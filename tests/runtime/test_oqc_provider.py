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

import pytest

try:
    from qcaas_client.client import OQCClient, QPUTask  # type: ignore

    from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
    from qbraid.runtime import DeviceType, TargetProfile
    from qbraid.runtime.enums import JobStatus
    from qbraid.runtime.oqc import OQCDevice, OQCJob, OQCProvider
    from qbraid.transpiler import ConversionScheme

    oqc_not_installed = False
except ImportError:
    oqc_not_installed = True

pytestmark = pytest.mark.skipif(oqc_not_installed, reason="qcaas_client not installed")

DEVICE_ID = "qpu:uk:2:d865b5a184"
FIXTURE_COUNT = sum(key in NATIVE_REGISTRY for key in ["qiskit", "braket", "cirq"])


@pytest.fixture
def oqc_device():
    """Return a fake OQC device."""

    class TestOQCClient:
        """Test class for OQC client."""

        def __init__(self, api_key):
            self.api_key = api_key

        def get_qpus(self):
            """Get QPUs."""
            return [
                {
                    "active": True,
                    "generation": 2,
                    "id": "qpu:uk:2:d865b5a184",
                    "name": "Lucy Simulator",
                    "region": "uk",
                    "url": "https://uk.cloud.oqc.app/d865b5a184",
                }
            ]

        def schedule_tasks(self, task: QPUTask, qpu_id: str):
            """Schedule tasks for the QPU."""
            qpu_id = qpu_id[::]
            return task
        
        def get_task_status(self, task_id: str, qpu_id: str):
            """Get task status."""
            return "COMPLETED"

        def get_task_metrics(self, task_id: str, qpu_id: str):
            """Get task metrics."""
            return {"optimized_circuit": "dummy", "optimized_instruction_count": 42}
        
        def get_task_errors(self, task_id: str, qpu_id: str):
            """Get task errors."""
            return None

    class TestOQCDevice(OQCDevice):
        """Test class for OQC device."""

        # pylint: disable-next=super-init-not-called
        def __init__(self, device_id, oqc_client=None):
            self._client = oqc_client or TestOQCClient("fake_api_key")
            self._profile = TargetProfile(
                device_id=device_id,
                device_type=DeviceType.SIMULATOR,
                num_qubits=8,
                program_spec=ProgramSpec(str, alias="qasm2"),
            )
            self._target_spec = ProgramSpec(str, alias="qasm2")
            self._scheme = ConversionScheme()

    return TestOQCDevice(DEVICE_ID)


def test_oqc_provider_device():
    """Test OQC provider and device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [{"id": DEVICE_ID, "num_qubits": 8}]
        provider = OQCProvider(api_key="fake_api_key")
        assert isinstance(provider, OQCProvider)
        assert isinstance(provider.client, OQCClient)
        assert provider.client == mock_client.return_value
        test_device = provider.get_device(DEVICE_ID)
        assert isinstance(test_device, OQCDevice)
        assert test_device.profile["device_id"] == DEVICE_ID


def test_build_runtime_profile():
    """Test building a runtime profile for OQC device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        provider = OQCProvider(api_key="fake_api_key")
        profile = provider._build_profile({"id": DEVICE_ID, "num_qubits": 8})
        assert isinstance(profile, TargetProfile)
        assert profile._data["device_id"] == DEVICE_ID
        assert profile._data["device_type"] == DeviceType.SIMULATOR
        assert profile._data["num_qubits"] == 8
        assert profile._data["program_spec"] == ProgramSpec(str, alias="qasm2")


@pytest.mark.parametrize("circuit", range(FIXTURE_COUNT), indirect=True)
def test_run_fake_job(circuit, oqc_device):
    """Test running a fake job."""
    job = oqc_device.run(circuit)
    assert isinstance(job, OQCJob)
    assert type(job.status()) == JobStatus
    assert type(job.metrics()) == dict
    assert type(job.metrics()["optimized_instruction_count"]) == int
    assert type(job.error()) == str
    


def test_run_batch_fake_job(run_inputs, oqc_device):
    """Test running a batch of fake jobs."""
    job = oqc_device.run(run_inputs)
    assert isinstance(job, list)
    assert len(job) == len(run_inputs)
    assert all(isinstance(j, OQCJob) for j in job)

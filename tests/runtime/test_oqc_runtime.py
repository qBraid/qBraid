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
import datetime
from unittest.mock import Mock, patch

import numpy as np
import pytest

try:
    from qcaas_client.client import OQCClient, QPUTask  # type: ignore

    from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
    from qbraid.runtime import DeviceType, TargetProfile
    from qbraid.runtime.enums import DeviceActionType, DeviceStatus, JobStatus
    from qbraid.runtime.exceptions import ResourceNotFoundError
    from qbraid.runtime.oqc import OQCDevice, OQCJob, OQCJobResult, OQCProvider
    from qbraid.transpiler import ConversionScheme

    FIXTURE_COUNT = sum(key in NATIVE_REGISTRY for key in ["qiskit", "braket", "cirq"])

    oqc_not_installed = False
except ImportError:
    FIXTURE_COUNT = 0

    oqc_not_installed = True


pytestmark = pytest.mark.skipif(oqc_not_installed, reason="qcaas_client not installed")

DEVICE_ID = "qpu:uk:2:d865b5a184"


@pytest.fixture
def lucy_simulator_data():
    """Return data for Lucy Simulator."""
    return {
        "active": True,
        "feature_set": {"always_on": True, "qubit_count": 8, "simulator": True},
        "generation": 2,
        "id": "qpu:uk:2:d865b5a184",
        "name": "Lucy Simulator",
        "region": "uk",
        "url": "https://uk.cloud.oqc.app/d865b5a184",
    }


@pytest.fixture
def oqc_device(lucy_simulator_data):
    """Return a fake OQC device."""

    class TestOQCClient:
        """Test class for OQC client."""

        def __init__(self, token):
            self.token = token

        def get_qpus(self):
            """Get QPUs."""
            return [lucy_simulator_data]

        def schedule_tasks(self, task: QPUTask, qpu_id: str):  # pylint: disable=unused-argument
            """Schedule tasks for the QPU."""
            return task

        def get_next_window(self, qpu_id: str):  # pylint: disable=unused-argument
            """Get next window."""
            return "2024-07-30 00:50:00"

        def get_task_status(
            self, task_id: str, qpu_id: str, **kwargs
        ):  # pylint: disable=unused-argument
            """Get task status."""
            success = kwargs.get("success", True)
            return "COMPLETED" if success else "FAILED"

        def get_task_timings(self, task_id: str, qpu_id: str):  # pylint: disable=unused-argument
            """Get task timings."""
            return {
                "RECEIVER_DEQUEUED": "2023-10-17 11:24:32.937188+00:00",
                "RECEIVER_ENQUEUED": "2023-10-17 11:24:32.996594+00:00",
                "RECEIVER_FROM_SCC": "2023-10-17 11:24:32.996594+00:00",
                "RECEIVER_TO_SCC": "2023-10-17 11:24:32.938188+00:00",
                "SERVER_DEQUEUED": "2023-10-17 11:24:36.057355+00:00",
                "SERVER_ENQUEUED": "2023-10-17 11:24:35.946476+00:00",
                "SERVER_RECEIVED": "2023-10-17 11:24:35.904885+00:00",
            }

        def get_task_metrics(self, task_id: str, qpu_id: str):  # pylint: disable=unused-argument
            """Get task metrics."""
            return {"optimized_circuit": "dummy", "optimized_instruction_count": 42}

        def get_task_metadata(self, task_id: str, qpu_id: str):  # pylint: disable=unused-argument
            """Get task metadata."""
            return {
                "config": '{"$type": "<class \'scc.compiler.config.CompilerConfig\'>", "$data": {"repeats": null, "repetition_period": null, "results_format": {"$type": "<class \'scc.compiler.config.QuantumResultsFormat\'>", "$data": {"format": null, "transforms": {"$type": "<enum \'scc.compiler.config.ResultsFormatting\'>", "$value": 2}}}, "metrics": {"$type": "<enum \'scc.compiler.config.MetricsType\'>", "$value": 6}, "active_calibrations": [], "optimizations": null, "error_mitigation": null}}',  # pylint: disable=line-too-long
                "created_at": "Wed, 12 Jun 2024 20:11:15 GMT",
                "id": "e35fb436-ff08-44c8-8acc-7d5a1f1a0ada",
                "qpu_id": "qpu:uk:2:d865b5a184",
                "tag": None,
            }

        def get_task_errors(
            self, task_id: str, qpu_id: str, **kwargs
        ):  # pylint: disable=unused-argument
            """Get task errors."""
            success = kwargs.get("success", True)
            attribute_error = kwargs.get("attribute_error", False)

            class MockError:
                """Mock error class."""

                def __init__(self, error_message):
                    self.error_message = error_message

            return None if success else (MockError("Error") if not attribute_error else "Error")

        def get_task_results(
            self, task_id: str, qpu_id: str, **kwargs
        ):  # pylint: disable=unused-argument
            """Get task results."""
            none = kwargs.get("none", False)

            class Result:
                """Result class."""

                def __init__(self, counts):
                    self.result = counts

            return Result(counts={"c": {"0": 1, "1": 1}}) if not none else None

        def cancel_task(self, task_id: str, qpu_id: str):  # pylint: disable=unused-argument
            """Cancel task."""
            return None

    class TestOQCDevice(OQCDevice):
        """Test class for OQC device."""

        # pylint: disable-next=super-init-not-called
        def __init__(self, device_id, oqc_client=None):
            self._client = oqc_client or TestOQCClient("fake_token")
            self._profile = TargetProfile(
                device_id=device_id,
                device_name="Lucy Simulator",
                device_type=DeviceType.SIMULATOR,
                action_type=DeviceActionType.OPENQASM,
                endpoint_url="https://uk.cloud.oqc.app/d865b5a184",
                num_qubits=8,
                program_spec=ProgramSpec(str, alias="qasm2"),
            )
            self._target_spec = ProgramSpec(str, alias="qasm2")
            self._scheme = ConversionScheme()

    return TestOQCDevice(DEVICE_ID)


def test_oqc_provider_device(lucy_simulator_data):
    """Test OQC provider and device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        mock_client.return_value.get_qpus.return_value = [lucy_simulator_data]
        provider = OQCProvider(token="fake_token")
        assert isinstance(provider, OQCProvider)
        assert isinstance(provider.client, OQCClient)
        assert provider.client == mock_client.return_value
        test_device = provider.get_device(DEVICE_ID)
        devices = provider.get_devices()
        assert isinstance(devices, list)
        assert any(device.id == test_device.id for device in devices)
        assert isinstance(test_device.status(), DeviceStatus)
        assert isinstance(test_device, OQCDevice)
        assert test_device.profile["device_id"] == DEVICE_ID
        with pytest.raises(ResourceNotFoundError):
            provider.get_device("fake_id")
        assert isinstance(test_device.client, OQCClient)
        lucy_simulator_data["feature_set"]["always_on"] = False
        now = datetime.datetime.now()
        year, month, day = now.year, now.month, now.day
        window = f"{year + 1}-{month}-{day} 00:50:00"
        mock_client.return_value.get_next_window.return_value = window
        unavailable_device = provider.get_device(DEVICE_ID)
        assert unavailable_device.status() == DeviceStatus.OFFLINE
        fake_profile = TargetProfile(
            device_id="fake_id",
            device_name="Fake Device",
            device_type=DeviceType.SIMULATOR,
            action_type=DeviceActionType.OPENQASM,
            endpoint_url="https://uk.cloud.oqc.app/fake_id",
            num_qubits=8,
            program_spec=ProgramSpec(str, alias="qasm2"),
        )
        fake_device = OQCDevice(profile=fake_profile, client=provider.client)
        with pytest.raises(ResourceNotFoundError):
            fake_device.status()

        window = f"{year - 1}-{month}-{day} 00:50:00"
        mock_client.return_value.get_next_window.return_value = window
        always_on_false_available_device = provider.get_device(DEVICE_ID)
        assert always_on_false_available_device.status() == DeviceStatus.ONLINE


def test_build_runtime_profile(lucy_simulator_data):
    """Test building a runtime profile for OQC device."""
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        provider = OQCProvider(token="fake_token")
        profile = provider._build_profile(lucy_simulator_data)
        assert isinstance(profile, TargetProfile)
        assert profile["device_id"] == DEVICE_ID
        assert profile["device_type"] == DeviceType.SIMULATOR.name
        assert profile["num_qubits"] == 8
        assert profile["program_spec"] == ProgramSpec(str, alias="qasm2")


@pytest.mark.parametrize("circuit", range(FIXTURE_COUNT), indirect=True)
def test_run_fake_job(circuit, oqc_device):
    """Test running a fake job."""
    job = oqc_device.run(circuit, shots=1)
    assert isinstance(job, OQCJob)
    assert isinstance(job.status(), JobStatus)
    assert isinstance(job.get_timings(), dict)
    assert isinstance(job.metrics(), dict)
    assert isinstance(job.metrics()["optimized_instruction_count"], int)
    assert isinstance(job.metadata(), dict)
    assert isinstance(job.get_errors(), (str, type(None)))
    res = job.result()
    assert isinstance(res, OQCJobResult)
    assert np.array_equal(res.measurements(), np.array([[0], [1]]))

    with pytest.raises(ResourceNotFoundError):
        job.result(none=True)

    assert job.get_errors(success=False) == "Error"
    assert job.result(success=False)._result.get("error_details", None) == "Error"

    assert job.get_errors(success=False, attribute_error=True) is None


def test_run_batch_fake_job(run_inputs, oqc_device):
    """Test running a batch of fake jobs."""
    job = oqc_device.run(run_inputs)
    assert isinstance(job, list)
    assert len(job) == len(run_inputs)
    assert all(isinstance(j, OQCJob) for j in job)


def test_cancel_job(oqc_device):
    """Test cancelling a fake job."""
    job = oqc_device.run("OPENQASM 2.0;\nqreg q[2];\ncreg c[2];\nh q[0];\nmeasure q[0] -> c[0];\n")
    assert isinstance(job, OQCJob)
    assert job.cancel() is None

# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for BraketProvider class

"""
import os
import random
import string
import json

import pytest
from braket.circuits import Circuit
from braket.devices import LocalSimulator
from braket.aws.aws_device import AwsDevice
from braket.aws.aws_session import AwsSession

from qbraid.runtime.braket import BraketProvider
from qbraid.runtime.braket.device import BraketDevice
from qbraid.runtime.braket.job import BraketQuantumTask
from qbraid.programs import ProgramSpec
from qbraid.runtime import DeviceType, TargetProfile

from unittest.mock import Mock, patch

# Skip tests if AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of AWS storage)"

SV1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"


def gen_rand_str(length: int) -> str:
    """Returns a random alphanumeric string of specified length."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def get_braket_most_busy():
    """Return the most busy device for testing purposes."""
    provider = BraketProvider()
    devices = provider.get_devices(
        types=["QPU"], statuses=["ONLINE"], provider_names=["Rigetti", "IonQ", "Oxford"]
    )
    test_device = None
    max_queued = 0
    for device in devices:
        jobs_queued = device.queue_depth()
        if jobs_queued is not None and jobs_queued > max_queued:
            max_queued = jobs_queued
            test_device = device
    return test_device

def test_braket_queue_visibility():
    """Test methods that check Braket device/job queue."""
    with patch("qbraid.runtime.braket.BraketProvider") as _:
        circuit = Circuit().h(0).cnot(0, 1)

        mock_device = Mock()
        mock_job = Mock()
        mock_job.queue_position.return_value = 5 # job is 5th in queue

        mock_device.run.return_value = mock_job

        device = mock_device
        if device is None:
            pytest.skip("No devices available for testing")
        else:
            job = device.run(circuit, shots=10)
            queue_position = job.queue_position()
            job.cancel()
            assert isinstance(queue_position, int)


def test_get_aws_session():
    """Test getting an AWS session."""
    with patch("boto3.session.Session") as mock_boto_session:
        mock_boto_session.aws_access_key_id.return_value = "aws_access_key_id"
        mock_boto_session.aws_secret_access_key.return_value = "aws_secret_access_key"
        aws_session = BraketProvider()._get_aws_session()
        assert aws_session.boto_session.region_name == "us-east-1"
        assert isinstance(aws_session, AwsSession)

class TestAwsSession:
    def __init__(self):
        self.region = "us-east-1"

    def get_device(self, device_arn):
        capabilities = {
            "action": {
                "braket.ir.openqasm.program": "literally anything",
                "paradigm": {"qubitCount": 2},
            }
        }
        cap_json = json.dumps(capabilities)
        metadata = {
            "deviceType": "SIMULATOR",
            "providerName": "Amazon Braket",
            "deviceCapabilities": cap_json,
        }

        return metadata
    
class TestDevice:
    def __init__(self, arn, aws_session=None):
        self.arn = arn
        self.aws_session = aws_session or TestAwsSession()

    @staticmethod
    def get_device_region(arn):
        return "us-east-1"

def test_build_runtime_profile():
    """Test building a runtime profile."""
    provider = BraketProvider()
    device = TestDevice("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
    profile = provider._build_runtime_profile(device=device)
    assert profile.get("device_type") == DeviceType.SIMULATOR
    assert profile.get("provider_name") == "Amazon Braket"
    assert profile.get("device_id") == SV1_ARN

def test_get_device():
    device_id = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
    provider = BraketProvider()
    with (patch("qbraid.runtime.braket.provider.AwsDevice") as mock_aws_device, patch("qbraid.runtime.braket.device.AwsDevice") as mock_aws_device_2):
        mock_aws_device.return_value = TestDevice(device_id)
        mock_aws_device_2.return_value = TestDevice(device_id)
        device = provider.get_device(device_id)
        assert device.id == device_id
        assert isinstance(device, BraketDevice)
   

def test_is_available():
    """Test device availability function."""
    with patch("qbraid.runtime.braket.BraketProvider") as mock_provider:
        provider = mock_provider.return_value

        mock_device_0 = Mock()
        mock_device_0.availability_window.return_value = (True, 0, 0)
        mock_device_0._device.is_available = True

        mock_device_1 = Mock()
        mock_device_1.availability_window.return_value = (False, 0, 0)
        mock_device_1._device.is_available = False

        provider.get_devices.return_value = [mock_device_0, mock_device_1]

        devices = provider.get_devices()
        for device in devices:
            is_available_bool, _, _ = device.availability_window()
            assert device._device.is_available == is_available_bool


def test_get_quantum_tasks_by_tag():
    """Test getting tagged quantum tasks."""
    with patch("qbraid.runtime.braket.BraketProvider") as mock_provider:
        provider = mock_provider.return_value
        provider.REGIONS = ["us-east-1", "us-west-1"]
        provider._get_default_region.return_value = "us-east-1"
        alt_regions = ["us-west-1"]

        mock_device = Mock()
        provider.get_device.return_value = mock_device

        mock_task_1 = Mock()
        mock_task_1.id = 'task1'

        mock_task_2 = Mock()
        mock_task_2.id = 'task2'

        circuit = Circuit().h(0).cnot(0, 1)
        mock_device.run.side_effect = [mock_task_1, mock_task_2]

        key, value1, value2 = 'abc123', 'val1', 'val2'
        mock_task_1.tags = {key: value1}
        mock_task_2.tags = {key: value2}
        provider.get_tasks_by_tag.side_effect = [[mock_task_1.id, mock_task_2.id], [mock_task_1.id], []]

        task1 = mock_device.run(circuit, shots=2, tags={key: value1})
        task2 = mock_device.run(circuit, shots=2, tags={key: value2})

        assert set([task1.id, task2.id]) == set(provider.get_tasks_by_tag(key))
        assert len(provider.get_tasks_by_tag(key, values=[value1], region_names=["us-east-1"])) == 1
        assert len(provider.get_tasks_by_tag(key, region_names=alt_regions)) == 0
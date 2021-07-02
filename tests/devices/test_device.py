"""
Unit tests for the qbraid device layer.
"""
import pytest
from qbraid.devices.aws.device import AWSDeviceWrapper
from braket.aws import AwsDevice
from braket.devices import LocalSimulator as AwsLocalSim




@pytest.mark.parametrize("provider,device", [("AWS", "test")])
def test_get_device_obj_aws(provider, device):
    qbraid_device = AWSDeviceWrapper(provider, device)
    aws_device = qbraid_device.root_device_obj
    assert isinstance(aws_device, AwsDevice)

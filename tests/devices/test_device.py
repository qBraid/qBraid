"""
Unit tests for the qbraid device layer.
"""
import pytest
from braket.devices import LocalSimulator as BraketSimulator
from cirq.devices.device import Device as CirqDevice
from abc import ABCMeta as QiskitDevice
from qbraid.devices.aws.device import BraketDeviceWrapper
from qbraid.devices.google.device import CirqDeviceWrapper
from qbraid.devices.ibm.device import QiskitDeviceWrapper
from qbraid.devices.utils import SUPPORTED_VENDORS
from qbraid.devices.utils import device_wrapper


def device_wrapper_inputs(vendor):
    input_list = []
    for provider in SUPPORTED_VENDORS[vendor]:
        for device in SUPPORTED_VENDORS[vendor][provider]:
            data = (device, provider, vendor)
            input_list.append(data)
    return input_list


inputs_init_braket_device_wrapper = device_wrapper_inputs("AWS")
inputs_init_cirq_device_wrapper = device_wrapper_inputs("Google")
inputs_init_qiskit_device_wrapper = device_wrapper_inputs("IBM")


@pytest.mark.parametrize("device,provider,vendor", inputs_init_braket_device_wrapper)
def test_init_braket_device_wrapper(device, provider, vendor):
    qbraid_device = device_wrapper(device, provider, vendor=vendor)
    vendor_device = qbraid_device.vendor_device_obj
    assert isinstance(qbraid_device, BraketDeviceWrapper)
    assert isinstance(vendor_device, BraketSimulator) or vendor_device is None


@pytest.mark.parametrize("device,provider,vendor", inputs_init_cirq_device_wrapper)
def test_init_cirq_device_wrapper(device, provider, vendor):
    qbraid_device = device_wrapper(device, provider, vendor=vendor)
    vendor_device = qbraid_device.vendor_device_obj
    assert isinstance(qbraid_device, CirqDeviceWrapper)
    assert isinstance(vendor_device, CirqDevice)


@pytest.mark.parametrize("device,provider,vendor", inputs_init_qiskit_device_wrapper)
def test_init_qiskit_device_wrapper(device, provider, vendor):
    qbraid_device = device_wrapper(device, provider, vendor=vendor)
    vendor_device = qbraid_device.vendor_device_obj
    assert isinstance(qbraid_device, QiskitDeviceWrapper)
    assert isinstance(vendor_device, QiskitDevice)

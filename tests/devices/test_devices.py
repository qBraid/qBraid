"""
Unit tests for the qbraid device layer.
"""
import pytest

from braket.devices import LocalSimulator as BraketSimulator
from qbraid.devices.aws.device import BraketDeviceWrapper

from cirq.devices.device import Device as CirqDevice
from qbraid.devices.google.device import CirqSamplerWrapper

import qiskit
from qiskit.providers.aer.aerjob import AerJob
from qiskit.providers import BackendV1 as QiskitBackend

from qbraid.devices.ibm.device import QiskitBackendWrapper
from qbraid.devices.ibm.job import QiskitJobWrapper
from qbraid.devices.utils import SUPPORTED_VENDORS
from qbraid.devices.utils import device_wrapper


def device_wrapper_inputs(vendor):
    input_list = []
    for provider in SUPPORTED_VENDORS[vendor]:
        for device in SUPPORTED_VENDORS[vendor][provider]:
            data = (device, provider, vendor)
            input_list.append(data)
    return input_list


inputs_braket_device_wrapper = device_wrapper_inputs("AWS")
inputs_cirq_device_wrapper = device_wrapper_inputs("Google")
inputs_qiskit_device_wrapper = device_wrapper_inputs("IBM")


@pytest.mark.parametrize("device,provider,vendor", inputs_braket_device_wrapper)
def test_init_braket_device_wrapper(device, provider, vendor):
    qbraid_device = device_wrapper(device, provider, vendor=vendor)
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, BraketDeviceWrapper)
    assert isinstance(vendor_device, BraketSimulator) or vendor_device is None


@pytest.mark.parametrize("device,provider,vendor", inputs_cirq_device_wrapper)
def test_init_cirq_device_wrapper(device, provider, vendor):
    qbraid_device = device_wrapper(device, provider, vendor=vendor)
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, CirqSamplerWrapper)
    assert isinstance(vendor_device, CirqDevice) or vendor_device is None


@pytest.mark.parametrize("device,provider,vendor", inputs_qiskit_device_wrapper)
def test_init_qiskit_device_wrapper(device, provider, vendor):
    qbraid_device = device_wrapper(device, provider, vendor=vendor)
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, QiskitBackendWrapper)
    assert isinstance(vendor_device, QiskitBackend) or vendor_device is None


@pytest.mark.parametrize("device,provider,vendor", [inputs_qiskit_device_wrapper[0]])
def test_run_qiskit_device_wrapper(device, provider, vendor):
    qbraid_device = device_wrapper(device, provider, vendor=vendor)
    circuit = qiskit.QuantumCircuit(3)  # Create a qiskit circuit
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(0, 2)
    qbraid_job = qbraid_device.run(circuit)
    vendor_job = qbraid_job.vendor_jlo
    assert isinstance(qbraid_job, QiskitJobWrapper)
    assert isinstance(vendor_job, AerJob)

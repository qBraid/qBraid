"""
Unit tests for the qbraid device layer.
"""
import pytest

from braket.devices import LocalSimulator as AwsSimulator
from braket.aws import AwsDevice
from qbraid.devices.aws.device import BraketDeviceWrapper

from cirq.sim.simulator_base import SimulatorBase as CirqSimulator
from qbraid.devices.google.device import CirqSimulatorWrapper

import qiskit
from qiskit.providers.aer.aerjob import AerJob
from qiskit.providers import BackendV1 as QiskitBackend

from qbraid.devices.ibm.device import QiskitBackendWrapper
from qbraid.devices.ibm.job import QiskitJobWrapper
from qbraid.devices._utils import SUPPORTED_VENDORS
from qbraid import device_wrapper


def device_wrapper_inputs(vendor):
    input_list = []
    for provider in SUPPORTED_VENDORS[vendor]:
        for device in SUPPORTED_VENDORS[vendor][provider]:
            data = (device, provider)
            input_list.append(data)
    return input_list


inputs_braket_dw = device_wrapper_inputs("AWS")
inputs_cirq_dw = device_wrapper_inputs("Google")
inputs_qiskit_dw = device_wrapper_inputs("IBM")


@pytest.mark.parametrize("device,provider", inputs_braket_dw)
def test_init_braket_device_wrapper(device, provider):
    qbraid_device = device_wrapper(device, provider, vendor="AWS")
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, BraketDeviceWrapper)
    assert isinstance(vendor_device, AwsSimulator) or isinstance(vendor_device, AwsDevice)


@pytest.mark.parametrize("device,provider", inputs_cirq_dw)
def test_init_cirq_device_wrapper(device, provider):
    qbraid_device = device_wrapper(device, provider, vendor="Google")
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, CirqSimulatorWrapper)
    assert isinstance(vendor_device, CirqSimulator)


@pytest.mark.parametrize("device,provider", inputs_qiskit_dw)
def test_init_qiskit_device_wrapper(device, provider):
    qbraid_device = device_wrapper(device, provider, vendor="IBM")
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, QiskitBackendWrapper)
    assert isinstance(vendor_device, QiskitBackend)


@pytest.mark.parametrize("device,provider", [inputs_qiskit_dw[0]])
def test_run_qiskit_device_wrapper(device, provider):
    qbraid_device = device_wrapper(device, provider, vendor="IBM")
    circuit = qiskit.QuantumCircuit(3)  # Create a qiskit circuit
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(0, 2)
    qbraid_job = qbraid_device.run(circuit)
    vendor_job = qbraid_job.vendor_jlo
    assert isinstance(qbraid_job, QiskitJobWrapper)
    assert isinstance(vendor_job, AerJob)

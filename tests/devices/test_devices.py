"""
Unit tests for the qbraid device layer.
"""
import pytest

from braket.devices import LocalSimulator as AwsSimulator
from braket.aws import AwsDevice
from qbraid.devices.aws.device import BraketDeviceWrapper

from cirq.sim.simulator_base import SimulatorBase as CirqSimulator
from qbraid.devices.google.device import CirqSimulatorWrapper

from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.providers.job import Job as QiskitJob
from qiskit.providers.backend import Backend as QiskitBackend

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

inputs_braket_run = []
inputs_cirq_run = []
inputs_qiskit_run = [
    ("least_busy_qpu", "IBMQ"), ("simulator_qasm", "BasicAer"), ("simulator_aer", "Aer")
]


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


@pytest.mark.parametrize("device,provider", inputs_qiskit_run)
def test_run_qiskit_device_wrapper(device, provider):
    qbraid_device = device_wrapper(device, provider, vendor="IBM")
    circuit = QiskitCircuit(1)
    circuit.h(0)
    circuit.y(0)
    circuit.measure_all()
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job.vendor_jlo
    assert isinstance(qbraid_job, QiskitJobWrapper)
    assert isinstance(vendor_job, QiskitJob)

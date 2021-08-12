"""
Unit tests for the qbraid device layer.
"""
import pytest
import numpy as np

from braket.circuits import Circuit as BraketCircuit
from braket.aws import AwsDevice
from braket.devices import LocalSimulator as AwsSimulator
from braket.tasks.quantum_task import QuantumTask as BraketQuantumTask
from dwave.system.composites import EmbeddingComposite

import cirq
from cirq.sim.simulator_base import SimulatorBase as CirqSimulator
from cirq.study.result import Result as CirqResult

from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.providers.backend import Backend as QiskitBackend
from qiskit.providers.job import Job as QiskitJob

from qbraid import device_wrapper
from qbraid.devices._utils import SUPPORTED_VENDORS
from qbraid.devices.aws import BraketDeviceWrapper, BraketQuantumTaskWrapper
from qbraid.devices.google import CirqSimulatorWrapper, CirqResultWrapper
from qbraid.devices.ibm import QiskitBackendWrapper, QiskitJobWrapper


def device_wrapper_inputs(vendor: str):
    """Returns list of tuples containing all device_wrapper inputs for given vendor."""
    input_list = []
    for provider in SUPPORTED_VENDORS[vendor]:
        for device in SUPPORTED_VENDORS[vendor][provider]:
            data = (device, provider)
            input_list.append(data)
    return input_list


"""
Device wrapper tests: initialization
Coverage: all vendors, all available devices
"""
inputs_braket_dw = device_wrapper_inputs("AWS")
inputs_braket_sampler = [("DW_2000Q_6", "D-Wave"), ("Advantage_system1", "D-Wave")]
inputs_cirq_dw = device_wrapper_inputs("Google")
inputs_qiskit_dw = device_wrapper_inputs("IBM")


@pytest.mark.parametrize("device,provider", inputs_braket_dw)
def test_init_braket_device_wrapper(device, provider):
    qbraid_device = device_wrapper(device, provider, vendor="AWS")
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, BraketDeviceWrapper)
    assert isinstance(vendor_device, AwsSimulator) or isinstance(vendor_device, AwsDevice)


@pytest.mark.parametrize("device,provider", inputs_braket_sampler)
def test_init_braket_dwave_sampler(device, provider):
    qbraid_device = device_wrapper(device, provider, vendor="AWS")
    vendor_sampler = qbraid_device.get_sampler()
    assert isinstance(vendor_sampler, EmbeddingComposite)


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


"""
Device wrapper tests: run method
Coverage: all vendors, one device from each provider (calls to QPU's take time)
"""


def braket_circuit():
    circuit = BraketCircuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
    return circuit


def cirq_circuit(meas=True):
    q0 = cirq.GridQubit(0, 0)

    def basic_circuit():
        yield cirq.H(q0)
        yield cirq.Ry(rads=np.pi / 2)(q0)
        if meas:
            yield cirq.measure(q0, key='q0')
    circuit = cirq.Circuit()
    circuit.append(basic_circuit())
    return circuit


def qiskit_circuit(meas=True):
    circuit = QiskitCircuit(1, 1) if meas else QiskitCircuit(1)
    circuit.h(0)
    circuit.ry(np.pi / 2, 0)
    if meas:
        circuit.measure(0, 0)
    return circuit


circuits_braket_run = [braket_circuit(), cirq_circuit(False), qiskit_circuit(False)]
circuits_cirq_run = [cirq_circuit(), qiskit_circuit()]
circuits_qiskit_run = circuits_cirq_run
inputs_braket_run = [("simulator_statevector", "AWS")]
inputs_cirq_run = [("local_simulator_densitymatrix", "Google")]
inputs_qiskit_run = [
    ("least_busy_qpu", "IBMQ"), ("simulator_qasm", "BasicAer"), ("simulator_aer", "Aer")
]


# Runtime ~3 seconds/test
@pytest.mark.parametrize("circuit", circuits_braket_run)
@pytest.mark.parametrize("device,provider", inputs_braket_run)
def test_run_qiskit_device_wrapper(device, provider, circuit):
    qbraid_device = device_wrapper(device, provider, vendor="AWS")
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job.vendor_jlo
    assert isinstance(qbraid_job, BraketQuantumTaskWrapper)
    assert isinstance(vendor_job, BraketQuantumTask)


@pytest.mark.parametrize("circuit", circuits_cirq_run)
@pytest.mark.parametrize("device,provider", inputs_cirq_run)
def test_run_cirq_device_wrapper(device, provider, circuit):
    qbraid_device = device_wrapper(device, provider, vendor="Google")
    qbraid_result = qbraid_device.run(circuit, repetitions=10)
    vendor_result = qbraid_result.vendor_rlo
    assert isinstance(qbraid_result, CirqResultWrapper)
    assert isinstance(vendor_result, CirqResult)


# Runtime ~3 seconds/test 6 tests,  ~20 seconds
@pytest.mark.parametrize("circuit", circuits_qiskit_run)
@pytest.mark.parametrize("device,provider", inputs_qiskit_run)
def test_run_qiskit_device_wrapper(device, provider, circuit):
    qbraid_device = device_wrapper(device, provider, vendor="IBM")
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job.vendor_jlo
    assert isinstance(qbraid_job, QiskitJobWrapper)
    assert isinstance(vendor_job, QiskitJob)



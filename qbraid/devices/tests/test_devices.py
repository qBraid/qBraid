"""
Unit tests for the qbraid device layer.
"""
import cirq
import numpy as np
import pytest
from braket.aws import AwsDevice
from braket.circuits import Circuit as BraketCircuit
from braket.circuits import Observable as BraketObservable
from braket.devices import LocalSimulator as AwsSimulator
from braket.tasks.quantum_task import QuantumTask as BraketQuantumTask
from cirq.sim.simulator_base import SimulatorBase as CirqSimulator
from cirq.study.result import Result as CirqResult

# from dwave.system.composites import EmbeddingComposite
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.providers.backend import Backend as QiskitBackend
from qiskit.providers.job import Job as QiskitJob

from qbraid import api, device_wrapper, retrieve_job, random_circuit
from qbraid.devices import DeviceError, JobError, ResultWrapper
from qbraid.devices.aws import (
    BraketDeviceWrapper,
    BraketLocalQuantumTaskWrapper,
    BraketLocalSimulatorWrapper,
    BraketQuantumTaskWrapper,
)
from qbraid.devices.google import CirqResultWrapper, CirqSimulatorWrapper
from qbraid.devices.ibm import (
    QiskitBackendWrapper,
    QiskitBasicAerJobWrapper,
    QiskitBasicAerWrapper,
    QiskitJobWrapper,
)


def device_wrapper_inputs(vendor: str):
    """Returns list of tuples containing all device_wrapper inputs for given vendor."""
    devices = api.get("/public/lab/get-devices", json={})
    input_list = []
    for document in devices:
        if document["vendor"] == vendor:
            input_list.append(document["qbraid_id"])
    return input_list


"""
Device wrapper tests: initialization
Coverage: all vendors, all available devices
"""

inputs_braket_dw = device_wrapper_inputs("AWS")
inputs_braket_sampler = ["aws_dwave_2000Q_6", "aws_dwave_advantage_system1"]
inputs_cirq_dw = ["google_cirq_sparse_sim", "google_cirq_dm_sim"]
inputs_qiskit_dw = device_wrapper_inputs("IBM")


@pytest.mark.parametrize("device_id", inputs_braket_dw)
def test_init_braket_device_wrapper(device_id):
    qbraid_device = device_wrapper(device_id)
    vendor_device = qbraid_device.vendor_dlo
    if device_id == "aws_braket_default_sim":
        assert isinstance(qbraid_device, BraketLocalSimulatorWrapper)
        assert isinstance(vendor_device, AwsSimulator)
    else:
        assert isinstance(qbraid_device, BraketDeviceWrapper)
        assert isinstance(vendor_device, AwsDevice)


@pytest.mark.skip(reason="Skipping b/c EmbeddingComposite not installed")
@pytest.mark.parametrize("device_id", inputs_braket_sampler)
def test_init_braket_dwave_sampler(device_id):
    qbraid_device = device_wrapper(device_id)
    vendor_sampler = qbraid_device.get_sampler()
    # assert isinstance(vendor_sampler, EmbeddingComposite)


@pytest.mark.parametrize("device_id", inputs_cirq_dw)
def test_init_cirq_device_wrapper(device_id):
    qbraid_device = device_wrapper(device_id)
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, CirqSimulatorWrapper)
    assert isinstance(vendor_device, CirqSimulator)


@pytest.mark.parametrize("device_id", inputs_qiskit_dw)
def test_init_qiskit_device_wrapper(device_id):
    qbraid_device = device_wrapper(device_id)
    vendor_device = qbraid_device.vendor_dlo
    if device_id[4:9] == "basic":
        assert isinstance(qbraid_device, QiskitBasicAerWrapper)
    else:
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
            yield cirq.measure(q0, key="q0")

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
inputs_cirq_run = ["google_cirq_dm_sim"]
# inputs_braket_run = ["aws_sv_sim", "aws_ionq", "aws_rigetti_aspen_9", "aws_braket_default_sim"]
inputs_qiskit_run = ["ibm_basicaer_qasm_sim", "ibm_aer_qasm_sim", "ibm_aer_default_sim"]
inputs_braket_run = ["aws_sv_sim", "aws_rigetti_aspen_11"]


@pytest.mark.parametrize("circuit", circuits_qiskit_run)
@pytest.mark.parametrize("device_id", inputs_qiskit_run)
def test_run_qiskit_device_wrapper(device_id, circuit):
    qbraid_device = device_wrapper(device_id)
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job.vendor_jlo
    if device_id[4:9] == "basic":
        assert isinstance(qbraid_job, QiskitBasicAerJobWrapper)
        with pytest.raises(JobError):
            qbraid_job.cancel()
    else:
        assert isinstance(qbraid_job, QiskitJobWrapper)
        qbraid_job.cancel()
    assert isinstance(vendor_job, QiskitJob)


@pytest.mark.parametrize("circuit", circuits_cirq_run)
@pytest.mark.parametrize("device_id", inputs_cirq_run)
def test_run_cirq_device_wrapper(device_id, circuit):
    qbraid_device = device_wrapper(device_id)
    qbraid_job = qbraid_device.run(circuit, shots=10)
    qbraid_result = qbraid_job.result()
    vendor_result = qbraid_result.vendor_rlo
    assert isinstance(qbraid_result, CirqResultWrapper)
    assert isinstance(vendor_result, CirqResult)


@pytest.mark.parametrize("circuit", circuits_braket_run)
@pytest.mark.parametrize("device_id", inputs_braket_run)
def test_run_braket_device_wrapper(device_id, circuit):
    qbraid_device = device_wrapper(device_id)
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job.vendor_jlo
    if device_id == "aws_braket_default_sim":
        assert isinstance(qbraid_job, BraketLocalQuantumTaskWrapper)
        assert isinstance(vendor_job, BraketQuantumTask)
        with pytest.raises(JobError):
            qbraid_job.cancel()
    else:
        assert isinstance(qbraid_job, BraketQuantumTaskWrapper)
        assert isinstance(vendor_job, BraketQuantumTask)


@pytest.mark.parametrize("device_id", ["aws_dm_sim", "aws_sv_sim"])
def test_run_braket_device_wrapper_no_shots(device_id):
    circuit = BraketCircuit().h(0).cnot(0, 1)
    if device_id == "aws_dm_sim":
        circuit.expectation(observable=BraketObservable.Z(), target=0)
    elif device_id == "aws_sv_sim":
        circuit.amplitude(state=["01", "10"])
    else:
        assert False
    qbraid_device = device_wrapper(device_id)
    qbraid_job = qbraid_device.run(circuit)  # Note: shots kwarg not provided
    vendor_job = qbraid_job.vendor_jlo
    assert isinstance(qbraid_job, BraketQuantumTaskWrapper)
    assert isinstance(vendor_job, BraketQuantumTask)


def test_circuit_too_many_qubits():
    two_qubit_circuit = QiskitCircuit(2)
    two_qubit_circuit.h([0, 1])
    two_qubit_circuit.cx(0, 1)
    one_qubit_device = device_wrapper("ibm_q_armonk")
    with pytest.raises(DeviceError):
        one_qubit_device.run(two_qubit_circuit)


def test_device_num_qubits():
    one_qubit_device = device_wrapper("ibm_q_armonk")
    assert one_qubit_device.num_qubits == 1
    simulator_device = device_wrapper("aws_braket_default_sim")
    assert simulator_device.num_qubits is None


@pytest.mark.skip(reason="Skipping b/c takes long time to finish")
@pytest.mark.parametrize("device_id", ["aws_sv_sim", "ibm_q_qasm_sim"])
def test_retrieve_job_ibmq(device_id):
    circuit = random_circuit("qiskit", num_qubits=1, depth=3, measure=True)
    qbraid_device = device_wrapper(device_id)
    qbraid_job = qbraid_device.run(circuit, shots=10)
    qbraid_job.wait_for_final_state()
    retrieved_job = retrieve_job(qbraid_job.id)
    assert qbraid_job.status() == retrieved_job.status()


@pytest.mark.parametrize("device_id", ["ibm_q_sv_sim", "aws_dm_sim", "google_cirq_dm_sim"])
def test_result_wrapper_measurements(device_id):
    circuit = random_circuit("qiskit", num_qubits=3, depth=3, measure=True)
    sim = device_wrapper(device_id).run(circuit, shots=10)
    qbraid_result = sim.result()
    assert isinstance(qbraid_result, ResultWrapper)
    measurements = qbraid_result.measurements()
    assert measurements.shape == (10, 3)


@pytest.mark.parametrize("device_id", ["aws_tn_sim", "aws_dm_sim", "aws_sv_sim"])
def test_cost_estimator(device_id):
    circuit = BraketCircuit().h(0).cnot(0, 1)
    estimate = device_wrapper(device_id).estimate_cost(circuit, shots=10)
    assert isinstance(estimate, float)

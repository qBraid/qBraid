"""
Unit tests for the qbraid device layer.
"""
import pytest

from qbraid import api, device_wrapper, random_circuit
from qbraid.devices import ResultWrapper

session = api.QbraidSession()

@pytest.mark.parametrize("device_id", ["ibm_q_sv_sim"])
def test_result_wrapper_measurements(device_id):
    circuit = random_circuit("qiskit", num_qubits=3, depth=3, measure=True)
    sim = device_wrapper(device_id).run(circuit, shots=10)
    qbraid_result = sim.result()
    assert isinstance(qbraid_result, ResultWrapper)
    measurements = qbraid_result.measurements()
    assert measurements.shape == (10, 3)
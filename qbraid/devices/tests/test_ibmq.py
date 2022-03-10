"""
Unit tests for the qbraid device layer.
"""
import pytest

from qiskit.providers.backend import Backend as QiskitBackend

from qbraid import api, device_wrapper
from qbraid.devices.ibm import QiskitBackendWrapper

session = api.QbraidSession()

def device_wrapper_inputs():
    """Returns list of tuples containing all device_wrapper inputs for given vendor."""
    devices = session.get("/public/lab/get-devices", params={}).json()
    input_list = []
    n = 0
    for document in devices:
        if document["vendor"] == "IBM" and n < 10:
            qbraid_id = document["qbraid_id"]
            if qbraid_id[:5] == "ibm_q":
                n += 1
                input_list.append(qbraid_id)
    return input_list

inputs_qiskit_dw = device_wrapper_inputs()


@pytest.mark.parametrize("device_id", inputs_qiskit_dw)
def test_init_qiskit_device_wrapper(device_id):
    qbraid_device = device_wrapper(device_id)
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, QiskitBackendWrapper)
    assert isinstance(vendor_device, QiskitBackend)
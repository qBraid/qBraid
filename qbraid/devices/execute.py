from ..circuits.transpiler import qbraid_wrapper
from ..circuits.circuit import AbstractCircuitWrapper


from .ibm.execute import _execute_ibm


from .google.execute import _execute_google


google_devices = ["device_a", "device_b"]
ibm_devices = ["qasm_simulator", "statevector_simulator"]


def execute(circuit, device: str, shots=1, **kwargs):

    # if circuit is not a qbraid wrapper, add the qbraid wrapper
    if not isinstance(circuit, AbstractCircuitWrapper):
        circuit = qbraid_wrapper(circuit)

    # get qBraid device object
    qbraid_device = get_qbraid_device(device)
    vendor = qbraid_device.vendor

    if vendor == "IBM":
        return _execute_ibm(circuit.transpile("qiskit"), device, **kwargs)
    elif vendor == "Google":
        return _execute_google(circuit.transpile("cirq"), device, **kwargs)
    else:
        raise TypeError("Cannot execute on devices from vendor {} yet".format(vendor))

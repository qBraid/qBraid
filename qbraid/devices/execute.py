from .google.execute import _execute_google
from .ibm.execute import _execute_ibm
from .getdevice import get_qbraid_device
from ..circuits.circuit import AbstractCircuitWrapper
from ..circuits.transpiler import qbraid_wrapper

google_devices = ["device_a", "device_b"]
ibm_devices = ["qasm_simulator", "statevector_simulator"]


def execute(circuit, device, **kwargs):

    # if circuit is not a qbraid wrapper, add the qbraid wrapper
    if not isinstance(circuit, AbstractCircuitWrapper):
        circuit = qbraid_wrapper(circuit)

    # get qBraid device object
    qbraid_device = get_qbraid_device(device)
    vendor = qbraid_device.vendor

    """Right now you can pass a device as a string or device object, this needs to be changed to
    ONLY allow device objects. Should add a function qbraid.device.get_supported_devices to show
    users which devices they can choose from, other something along those lines."""

    if vendor == "IBM":
        qiskit_circuit = circuit.transpile("qiskit")
        return _execute_ibm(qiskit_circuit, qbraid_device, **kwargs)
    elif vendor == "Google":
        cirq_circuit = circuit.transpile("cirq")
        return _execute_google(cirq_circuit, device, **kwargs)
    else:
        raise TypeError("Cannot execute on devices from vendor {} yet".format(vendor))

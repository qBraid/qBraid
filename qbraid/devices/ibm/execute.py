from qiskit import execute as qiskit_execute
from .devices import IBMAerDevice, IBMQDevice
from .result import IBMAerResult


def _execute_ibm(circuit, device, **kwargs):

    job = qiskit_execute(circuit, device.backend, **kwargs)
    result = job.result()

    if isinstance(device, IBMAerDevice):
        return IBMAerResult(result)
    elif isinstance(device, IBMQDevice):
        raise NotImplementedError
    else:
        raise NotImplementedError

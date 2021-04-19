from .result import IBMAerResult
from .devices import IBMAerDevice, IBMQDevice

from qiskit import execute as qiskit_execute


def _execute_ibm(qiskit_circuit, 
                 device,
                 shots = 1,
                 **kwargs):
    
    job = qiskit_execute(qiskit_circuit, device.backend, **kwargs )
    
    if isinstance(device, IBMAerDevice):
        return IBMAerResult(job)
    
    elif isinstance(device, IBMQDevice):
        pass
    


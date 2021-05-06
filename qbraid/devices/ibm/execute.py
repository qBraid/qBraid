from qiskit import execute as qiskit_execute

from .result import get_ibm_result

def _execute_ibm(qiskit_circuit, 
                 device,
                 shots = 1,
                 **kwargs):
    
    job = qiskit_execute(qiskit_circuit, device.backend, **kwargs )
    
    return get_ibm_result(device,job)
    
    


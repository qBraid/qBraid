import numpy as np
import pytest
import string

import qbraid
import pyquil

#############
### UTILS ###
#############

def generate_params(varnames):
    params = {}
    rot_args = ['angle', 'phi', 'lam', 'gamma']
    for ra in rot_args:
        if ra in varnames:
            params[ra] = np.random.rand() * 2 * np.pi
            
    if 'qubit' in varnames:
        params['qubit'] = 0
        
    if 'control' in varnames:
        params['control'] = 0
        params['target'] = 1
        
    if 'q1' in varnames:
        params['q1'] = 0
        params['q2'] = 1    
        
    return params

def get_pyquil_gates():
    pyquil_gates = {attr: None for attr in dir(pyquil.gates) if attr[0] in string.ascii_uppercase}

    for gate in pyquil_gates:
        try:
            params =  generate_params(getattr(pyquil.gates, gate).__code__.co_varnames)
            pyquil_gates[gate] = getattr(pyquil.gates, gate)(**params)        
        except Exception as e:
            continue

    return {k:v for k,v in pyquil_gates.items() if v is not None}


#############
### TESTS ###
#############

TARGETS = ['cirq', 'braket', 'qiskit', 'pytket']
pyquil_gates = get_pyquil_gates()
paramslist = [(target, gate) for target in TARGETS for gate in pyquil_gates]

@pytest.mark.parametrize("target, gate_name", paramslist)
def test_convert_from_pyquil_to_x(target, gate_name):
    gate = pyquil_gates[gate_name]
    source_circuit = pyquil.Program()
    source_circuit += gate
    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)            



import numpy as np
import scipy
import pytest
import string

import qbraid
import braket

#############
### UTILS ###
#############

def generate_params(varnames):
    params = {} 
    for v in varnames:
        if v.startswith('angle'):
            params[v] = np.random.rand() * 2 * np.pi
    return params

def get_braket_gates():
    braket_gates = {attr: None for attr in dir(braket.circuits.Gate) if attr[0] in string.ascii_uppercase}

    for gate in ['C', 'PulseGate']:
        braket_gates.pop(gate)
        
    for gate in braket_gates:
        if gate == 'Unitary':
            n = np.random.randint(1, 4)
            unitary = scipy.stats.unitary_group.rvs(2**n)
            braket_gates[gate] = getattr(braket.circuits.Gate, gate)(matrix=unitary) 
        else:
            params = generate_params(getattr(braket.circuits.Gate, gate).__init__.__code__.co_varnames)
            braket_gates[gate] = getattr(braket.circuits.Gate, gate)(**params)
    return {k:v for k,v in braket_gates.items() if v is not None}

#############
### TESTS ###
#############

TARGETS = ['cirq', 'qiskit', 'pyquil', 'pytket']
braket_gates = get_braket_gates()
paramslist = [(target, gate) for target in TARGETS for gate in braket_gates]

@pytest.mark.parametrize("target, gate_name", paramslist)
def test_convert_from_braket_to_x(target, gate_name):
    gate = braket_gates[gate_name]

    if gate.qubit_count == 1:
        source_circuit = braket.circuits.Circuit([braket.circuits.Instruction(gate, 0)])
    else:
        source_circuit = braket.circuits.Circuit([braket.circuits.Instruction(gate, range(gate.qubit_count))])
        
    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)            



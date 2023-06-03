import numpy as np
import scipy
import pytest
import string

import braket
from qbraid.devices.aws.ionq import braket_ionq_compilation

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

braket_gates = get_braket_gates()

@pytest.mark.parametrize("gate_name", braket_gates)
def test_braket_ionq_compilation(gate_name):
    gate = braket_gates[gate_name]

    if gate.qubit_count == 1:
        source_circuit = braket.circuits.Circuit([braket.circuits.Instruction(gate, 0)])
    else:
        source_circuit = braket.circuits.Circuit([braket.circuits.Instruction(gate, range(gate.qubit_count))])

    braket_ionq_compilation(source_circuit) # the function already has an assertion which checks that the predicates are satistfied

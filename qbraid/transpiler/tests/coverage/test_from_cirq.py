import numpy as np
import pytest
import string

import qbraid
import cirq

#############
### UTILS ###
#############

def generate_params(varnames):
    params = {}
    rot_args = ['rads']
    for ra in rot_args:
        if ra in varnames:
            params[ra] = np.random.rand() * 2 * np.pi
            
    if 'exponent' in varnames:
        params['exponent'] = np.random.rand() * 10
        
    if 'num_qubits' in varnames:
        params['num_qubits'] = np.random.randint(1, 7)
        
    return params

def get_cirq_gates():
    qubits = cirq.LineQubit.range(7)

    cirq_gates = {attr: None for attr in dir(cirq.ops.common_gates) if attr[0] in string.ascii_uppercase if  (isinstance(getattr(cirq.ops.common_gates, attr), cirq.value.abc_alt.ABCMetaImplementAnyOneOf) or isinstance(getattr(cirq.ops.common_gates, attr), cirq.Gate))}

    for gate in cirq_gates:
        params = generate_params(getattr(cirq.ops.common_gates, gate).__init__.__code__.co_varnames)
        if not isinstance(getattr(cirq.ops.common_gates, gate), cirq.Gate):
            cirq_gates[gate] = getattr(cirq.ops.common_gates, gate)(**params)

    for gate in cirq_gates:
        if cirq_gates.get(gate):
            cirq_gates[gate] = cirq_gates[gate](*qubits[:cirq_gates[gate].num_qubits()])
        else:
            cirq_gates[gate] = getattr(cirq.ops.common_gates, gate)(*qubits[:getattr(cirq.ops.common_gates, gate).num_qubits()])
    return {k:v for k,v in cirq_gates.items() if v is not None}

#############
### TESTS ###
#############

TARGETS = ['qiskit', 'braket', 'pyquil', 'pytket']
cirq_gates = get_cirq_gates()
paramslist = [(target, gate) for target in TARGETS for gate in cirq_gates]

@pytest.mark.parametrize("target, gate_name", paramslist)
def test_convert_from_cirq_to_x(target, gate_name):
    gate = cirq_gates[gate_name]
    source_circuit = cirq.Circuit()
    source_circuit.append(gate)
    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)            



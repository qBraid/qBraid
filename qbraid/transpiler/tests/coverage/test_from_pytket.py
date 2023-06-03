import numpy as np
import pytest
import string

import qbraid
import pytket

#############
### UTILS ###
#############

# I didn't find a way to generate the params
# dynamically because pytket method are wrapper around C++ code
gates_param_map = {
 'H': {'qubit': 0},
 'S': {'qubit': 0},
 'SX': {'qubit': 0},
 'SXdg': {'qubit': 0},
 'Sdg': {'qubit': 0},
 'T': {'qubit': 0},
 'Tdg': {'qubit': 0},
 'V': {'qubit': 0},
 'Vdg': {'qubit': 0},
 'X': {'qubit': 0},
 'Y': {'qubit': 0},
 'Z': {'qubit': 0},  
    
 'Phase': {'arg0': np.random.rand() * 2 * np.pi},
    
 'Rx': {'angle': np.random.rand() * 2 * np.pi, 'qubit': 0},
 'Ry': {'angle': np.random.rand() * 2 * np.pi, 'qubit': 0},
 'Rz': {'angle': np.random.rand() * 2 * np.pi, 'qubit': 0},
 'U1': {'angle': np.random.rand() * 2 * np.pi, 'qubit': 0},
    
 'ECR': {'qubit_0': 0, 'qubit_1': 1},
 'SWAP': {'qubit_0': 0, 'qubit_1': 1},
    
 'ISWAPMax': {'qubit0': 0, 'qubit1': 1},
 'Sycamore': {'qubit0': 0, 'qubit1': 1},  
 'ZZMax':  {'qubit0': 0, 'qubit1': 1},
    
 'CH': {'control_qubit':0, 'target_qubit': 1},
 'CSX': {'control_qubit':0, 'target_qubit': 1},
 'CSXdg': {'control_qubit':0, 'target_qubit': 1},
 'CV': {'control_qubit':0, 'target_qubit': 1},
 'CVdg': {'control_qubit':0, 'target_qubit': 1},
 'CX': {'control_qubit':0, 'target_qubit': 1},
 'CY': {'control_qubit':0, 'target_qubit': 1},
 'CZ': {'control_qubit':0, 'target_qubit': 1},
    
 'CCX': {'control_0': 0, 'control_1': 1, 'target': 2},
 
 'CSWAP': {'control': 0, 'target_0': 1, 'target_1': 2},

 'Measure': {'qubit': 0, 'bit_index': 0},
    
 'CRx': {'angle': np.random.rand() * 2 * np.pi, 'control_qubit': 0, 'target_qubit': 1},
 'CRy': {'angle': np.random.rand() * 2 * np.pi, 'control_qubit': 0, 'target_qubit': 1},
 'CRz': {'angle': np.random.rand() * 2 * np.pi, 'control_qubit': 0, 'target_qubit': 1},
 'CU1': {'angle': np.random.rand() * 2 * np.pi, 'control_qubit': 0, 'target_qubit': 1},
    
 'CU3': {'angle0': np.random.rand() * 2 * np.pi, 'angle1': np.random.rand() * 2 * np.pi, 'angle2': np.random.rand() * 2 * np.pi, 'control_qubit': 0, 'target_qubit': 1},
 
 'ESWAP': {'angle': np.random.rand() * 2 * np.pi, 'qubit0': 0, 'qubit1': 1},
 'ISWAP': {'angle': np.random.rand() * 2 * np.pi, 'qubit0': 0, 'qubit1': 1},
    
 'FSim': {'angle0': np.random.rand() * 2 * np.pi, 'angle1': np.random.rand() * 2 * np.pi, 'qubit0': 0, 'qubit1': 1},
 'PhasedISWAP': {'angle0': np.random.rand() * 2 * np.pi, 'angle1': np.random.rand() * 2 * np.pi, 'qubit0': 0, 'qubit1': 1},
    
 'PhasedX': {'angle0': np.random.rand() * 2 * np.pi, 'angle1': np.random.rand() * 2 * np.pi, 'qubit': 0},
 'U2': {'angle0': np.random.rand() * 2 * np.pi, 'angle1': np.random.rand() * 2 * np.pi, 'qubit': 0},

 'TK1': {'angle0': np.random.rand() * 2 * np.pi, 'angle1': np.random.rand() * 2 * np.pi, 'angle2': np.random.rand() * 2 * np.pi, 'qubit': 0},
 'U3': {'angle0': np.random.rand() * 2 * np.pi, 'angle1': np.random.rand() * 2 * np.pi, 'angle2': np.random.rand() * 2 * np.pi, 'qubit': 0},
 
 'TK2': {'angle0': np.random.rand() * 2 * np.pi, 'angle1': np.random.rand() * 2 * np.pi, 'angle2': np.random.rand() * 2 * np.pi, 'qubit0': 0, 'qubit1': 1},
 
 'XXPhase': {'angle': np.random.rand() * 2 * np.pi, 'qubit0': 0, 'qubit1': 1},
 'YYPhase': {'angle': np.random.rand() * 2 * np.pi, 'qubit0': 0, 'qubit1': 1},
 'ZZPhase': {'angle': np.random.rand() * 2 * np.pi, 'qubit0': 0, 'qubit1': 1},
    
 'XXPhase3': {'angle': np.random.rand() * 2 * np.pi, 'qubit0': 0, 'qubit1': 1, 'qubit2': 2}
}


def get_pytket_circuits():
    pytket_gates = {attr: None for attr in dir(pytket.Circuit) if attr[0] in string.ascii_uppercase}
    for gate in pytket_gates:
        try:
            if gates_param_map[gate] is None:
                continue
            pytket_gates[gate] = getattr(pytket.Circuit(3, 1), gate)(**gates_param_map[gate])
        except Exception as e:
            print(e)
    return {k:v for k,v in pytket_gates.items() if v is not None}

#############
### TESTS ###
#############

TARGETS = ['cirq', 'braket', 'pyquil', 'qiskit']
pytket_circuits = get_pytket_circuits()
paramslist = [(target, circuit) for target in TARGETS for circuit in pytket_circuits]

@pytest.mark.parametrize("target, circuit_name", paramslist)
def test_convert_from_pytket_to_x(target, circuit_name):
    source_circuit = pytket_circuits[circuit_name]
    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)            



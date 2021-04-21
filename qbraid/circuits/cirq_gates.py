# =============================================================================
# from typing import Iterable, Union
# import numpy as np
# from numpy import pi, sin, cos, exp, sqrt
# 
# #gate types
# from cirq import Gate as CirqGate
# from cirq.ops.gate_features import SingleQubitGate as CirqSingleQubitGate
# from cirq.ops.gate_features import TwoQubitGate as CirqTwoQubitGate
# from cirq.ops.gate_features import ThreeQubitGate as CirqThreeQubitGate
# import cirq
# 
# #standard gates
# #import cirq.ops.PhasedXPowGate
# from cirq.ops.common_gates import (
#     XPowGate as CirqXPowGate, 
#     YPowGate as CirqYPowGate,
#     ZPowGate as CirqZPowGate,
#     HPowGate as CirqHPowGate,
#     CZPowGate as CirqCZPowGate,
#     CXPowGate as CirqCXPowGate,
# )
# #PhasedXPowGate as CirqPhasedPowGate
# from cirq.ops.swap_gates import (
#     ISWAP as CirqiSwap, 
#     SWAP as CirqSwap, 
#     ISwapPowGate as CirqISwapPowGate, 
#     SwapPowGate as CirqSwapPowGate,
# )
# from cirq.ops.common_gates import (
#     rx as cirq_rx,
#     ry as cirq_ry,
#     rz as cirq_rz,
#     cphase as cirq_cphase,
# )
# from cirq.ops.three_qubit_gates import (
#     CCZPowGate as CirqCCZPowGate,
#     CCXPowGate as CirqCCXPowGate,
#     CSwapGate as CirqCSwapGate,
# )
# from cirq.ops.controlled_gate import ControlledGate as CirqControlledGate
# from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure
# 
# 
# 
# 
# 
# 
# 
# 
# 
# #custom gate definitions -----------------------------------------
# class CirqU3Gate(CirqSingleQubitGate):
#     
#     def __init__(self, theta, phi, lam):
#         
#         self._theta = theta
#         self._phi = phi
#         self._lam = lam
#     
#         super(CirqU3Gate, self)
#     
#     def _unitary_(self):
#         
#         c = cos(self._theta/2)
#         s = sin(self._theta/2)
#         phi = self._phi
#         lam = self._lam
#         
#         
#         return np.array([
#             [c, -exp(complex(0,lam))*s],
#             [exp(complex(0,phi))*s, exp(complex(0,phi+lam))*c]
#         ])
#     
#     def _circuit_diagram_info_(self, args):
#         return "U3"
#         
# class CirqUnitaryGate(CirqGate):
#     
#     def __init__(self, matrix: np.ndarray, name: str = 'U'):
#         
#         self._name = name
#         self._matrix = matrix
#         super(CirqUnitaryGate, self)
#     
#     def _num_qubits_(self):
#         return int(np.log2(len(self._matrix)))
#     
#     def _unitary_(self):
#         return self._matrix
#     
#     def _circuit_diagram_info_(self, args):
#         n= self._num_qubits_()
#         symbols = [self._name for _ in range(n)]
#         return symbols
#     
# cirq_gates = {
#         'H': CirqHPowGate,
#         'X': CirqXPowGate,
#         'Y': CirqYPowGate,
#         'Z': CirqZPowGate,
#         'S': CirqZPowGate,
#         #'Sdg': ,
#         'T': CirqZPowGate,
#         #'Tdg': ,
#         # I
#         # SX
#         # SXdg
#         'HPow': CirqHPowGate,
#         'XPow': CirqXPowGate,
#         'YPow': CirqYPowGate,
#         'ZPow': CirqZPowGate,
#         'RX': cirq_rx,
#         'RY': cirq_ry,
#         'RZ': cirq_rz,
#         'Phase': CirqZPowGate,
#         'U1': CirqZPowGate,
#         'CX': CirqCXPowGate,
#         'Swap': CirqSwap,
#         'iSwap': CirqiSwap,
#         'CZ': CirqCZPowGate,
#         'CPhase': cirq_cphase,
#         'CCZ': CirqCCZPowGate,
#         'CCX': CirqCCXPowGate,
#         'MEASURE': CirqMeasure,
#         'U3': CirqU3Gate,
#         'Unitary': CirqUnitaryGate
#     }
# 
# 
# 
# 
# 
# #types = (c for c in cirq_gates.values())
# CirqGateTypes = None #Union[*types]
# 
# CirqGate = Union[CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate,CirqMeasure]
# 
# 
# def get_cirq_gate_data(gate: CirqGate):
#     
#     data = {
#         'type': None,
#         'params': [],
#         'matrix':None,
#         'num_controls':0
#         }
#     
#     try:
#         data['matrix'] = cirq.unitary(gate)
#     except:
#         pass
#     
#     # measurement gate
#     if isinstance(gate,CirqMeasure):
#         #add info self.measurement_map
#         data['type'] = 'MEASURE'
#     
#     # single qubit gates
#     elif isinstance(gate, CirqHPowGate):
#         if gate.exponent == 1:
#             data['type'] = 'H'
#         else:
#             data['type'] = 'HPow'
#             
#             t = gate.exponent
#             data['params'] = [t]
#         
#             
#     elif isinstance(gate, CirqXPowGate):
#         if gate.exponent ==1:
#             data['type'] = 'X'
#         elif gate.global_shift== -0.5:
#             params = [gate.exponent*np.pi]
#             data['type'] = 'RX'
#             data['params'] = params   
#         else:
#             data['type'] = 'XPow'
#             
#             t = gate.exponent
#             data['params'] = [t]
#     
#             
#     elif isinstance(gate, CirqYPowGate):
#         if gate.exponent == 1:
#             data['type'] = 'Y'
#         else:
#             data['type'] = 'YPow'
#             
#             t = gate.exponent
#             data['params'] = [t]
#             
#             
#     elif isinstance(gate, CirqZPowGate):
#         if gate.exponent == 1:
#             data['type'] = 'Z'
#         elif gate.exponent == 0.5:
#             data['type'] = 'S'
#         elif gate.exponent == 0.25:
#             data['type'] = 'T'
#         else:
#             data['type'] = 'Phase'
#             
#             t = gate.exponent
#             lam = t*pi
#             data['params'] = [lam]
#             
#             
#     #two qubit gates
#     elif isinstance(gate, CirqCXPowGate):
#         if gate.exponent ==1:
#             data['type'] = 'CX'
#         else:
#             data['type'] = 'CXPow'
#     elif isinstance(gate, CirqCZPowGate):
#         if gate.exponent ==1:
#             data['type'] = 'CZ'
#         else:
#             data['type'] = 'CZPow'
#     #three qubit gates
#     elif isinstance(gate, CirqCCZPowGate):
#         if gate.exponent == 1:
#             data['type'] = 'CCZ'
#         else:
#             data['type'] = 'CCZPow'
#     elif isinstance(gate, CirqCCXPowGate):
#         if gate.exponent == 1:
#             data['type'] = 'CCX'
#         else:
#             pass
#     elif isinstance(gate, CirqCSwapGate):
#         data['type'] = 'CSwap'
#         
#     elif isinstance(gate, CirqControlledGate):
#         data['type'] = 'Controlled'
#         data['base_gate_data'] = get_cirq_gate_data(gate.sub_gate)
#         data['num_controls'] = gate.num_controls()
#         
#     else:
#         print(type(gate))
#         print(gate)
#         raise TypeError("Could not determined gate type.")
#         
#     return data
#         
# def create_cirq_gate(data):
#     
#     gate_type = data['type']
#     params = data['params']
# 
#     #single-qubit, no parameters
#     if gate_type in ('H','X','Y','Z'):
#         return cirq_gates[gate_type]()
#     
#     elif gate_type == 'S':
#         return cirq_gates['S'](exponent=0.5)
#     elif gate_type == 'T':
#         return cirq_gates['T'](exponent=0.25)
#     
#     # single-qubit, one-parameter gates
#     elif gate_type in ('RX','RY','RZ'):
#         theta = data['params'][0]/pi
#         return cirq_gates[gate_type](theta)
#         
#     elif gate_type == 'Phase':
#         t = data['params'][0]/pi
#         return cirq_gates['Phase'](exponent=t)
#     
#     #two-qubit, no parameters
#     elif gate_type in ('CX','CZ'):
#         return cirq_gates[gate_type]() #default exponent = 1 
#     
#     elif gate_type in ('CPhase'):
#         return cirq_gates[gate_type](data['params'][0])
#     
#     elif gate_type in ('Swap','iSwap'):
#         return cirq_gates[gate_type]
#     
#     #multi-qubit
#     elif gate_type in ('CCX'):
#         return cirq_gates[gate_type]()
#         
#     #measure
#     elif gate_type == 'MEASURE':
#         return 'CirqMeasure'
#     
#     #custom gates
#     elif gate_type == 'U3':
#         return CirqU3Gate(*params)
#     
#     elif gate_type == 'Unitary':
#         if data['name'] == 'Unitary':
#             data['name'] == 'U'
#         return cirq_gates['Unitary'](data['matrix'], name = data['name'])
#     
#     #error
#     else:
#         print(gate_type)
#         raise TypeError("Gate type not handled")
# =============================================================================

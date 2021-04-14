from typing import Iterable
import numpy as np

#qiskit gate types
from qiskit.circuit.gate import Gate as QiskitGate
from qiskit.circuit.controlledgate import ControlledGate as QiskitControlledGate

#qiskit standard gates

from qiskit.circuit.library.standard_gates.h import (
    HGate as QiskitHGate,
    CHGate as QiskitCHGate)
from qiskit.circuit.library.standard_gates.x import (
    XGate as QiskitXGate,
    CXGate as QiskitCXGate,
    RCCXGate as QiskitRCCXGate,
    RC3XGate as QiskitRC3XGate,
    CCXGate as QiskitCCXGate,
    MCXGrayCode as QiskitMCXGrayCodeGate, 
    MCXRecursive as QiskitMCXRecursiveGate, 
    MCXVChain as QiskitMCXVChainGate)
from qiskit.circuit.library.standard_gates.y import (
    YGate as QiskitYGate,
    CYGate as QiskitCYGate)
from qiskit.circuit.library.standard_gates.z import (
    ZGate as QiskitZGate,
    CZGate as QiskitCZGate)
from qiskit.circuit.library.standard_gates.p import (
    PhaseGate as QiskitPhaseGate,
    CPhaseGate as QiskitCPhaseGate,
    MCPhaseGate as QiskitMCPhaseGate,
    )
from qiskit.circuit.library.standard_gates.ry import (
    RYGate as QiskitRYGate,
    CRYGate as QiskitCRYGate)

from qiskit.circuit.library.standard_gates.rz import (
    RZGate as QiskitRZGate,
    CRZGate as QiskitCRZGate)
from qiskit.circuit.library.standard_gates.rx import (
    RXGate as QiskitRXGate,
    CRXGate as QiskitCRXGate)
from qiskit.circuit.library.standard_gates.r import RGate as QiskitRGate
from qiskit.circuit.library.standard_gates.rxx import RXXGate as QiskitRXXGate
from qiskit.circuit.library.standard_gates.ryy import RYYGate as QiskitRYYGate
from qiskit.circuit.library.standard_gates.rzx import RZXGate as QiskitRZXGate
from qiskit.circuit.library.standard_gates.rzz import RZZGate as QiskitRZZGate
from qiskit.circuit.library.standard_gates.dcx import DCXGate as QiskitDCXGate
from qiskit.circuit.library.standard_gates.iswap import iSwapGate as QiskitiSwapGate
from qiskit.circuit.measure import Measure as QiskitMeasurementGate
from qiskit.circuit.library.standard_gates.i import IGate as QiskitIGate
from qiskit.circuit.library.generalized_gates.gms import MSGate as QiskitMSGate

from qiskit.circuit.library.standard_gates.s import (
    SGate as QiskitSGate,
    SdgGate as QiskitSdgGate)
from qiskit.circuit.library.standard_gates.swap import (
    SwapGate as QiskitSwapGate,
    CSwapGate as QiskitCSwapGate)

from qiskit.circuit.library.standard_gates.sx import (
    SXGate as QiskitSXGate,
    SXdgGate as QiskitSXdgGate,
    CSXGate as QiskitCSXGate)
from qiskit.circuit.library.standard_gates.t import (
    TGate as QiskitTGate,
    TdgGate as QiskitTdgGate)
from qiskit.circuit.library.standard_gates.u import (
    UGate as QiskitUGate,
    CUGate as QiskitCUGate)
from qiskit.circuit.library.standard_gates.u1 import (
    U1Gate as QiskitU1Gate,
    CU1Gate as QiskitCU1Gate,
    MCU1Gate as QiskitMCU1Gate)
from qiskit.circuit.library.standard_gates.u2 import U2Gate as QiskitU2Gate
from qiskit.circuit.library.standard_gates.u3 import (
    U3Gate as QiskitU3Gate,
    CU3Gate as QiskitCU3Gate)
from qiskit.extensions.unitary import UnitaryGate as QiskitUnitaryGate


def get_qiskit_gate_data(gate: QiskitGate):
    
    data = {
        'type': None,
        'params': gate.params,
        'matrix': None,
        'num_controls':0
    }
    try: 
        data['matrix'] = gate.to_matrix()
    except:
        pass
    
    #measurement
    if isinstance(gate,QiskitMeasurementGate):        
        data['type'] = 'MEASURE'
    
    #single-qubit gates, no parameters
    elif isinstance(gate,QiskitHGate):
        data['type'] =  'H'
    elif isinstance(gate,QiskitXGate):
        data['type'] =  'X'
    elif isinstance(gate,QiskitYGate):
        data['type'] =  'Y'
    elif isinstance(gate,QiskitZGate):
        data['type'] =  'Z'
    elif isinstance(gate,QiskitSGate):
        data['type'] =  'S'
    elif isinstance(gate,QiskitSdgGate):
        data['type'] =  'Sdg'
    elif isinstance(gate,QiskitTGate):
        data['type'] =  'T'
    elif isinstance(gate,QiskitTdgGate):
        data['type'] =  'Tdg'
    elif isinstance(gate,QiskitIGate):
        data['type'] =  'I'
    elif isinstance(gate,QiskitSXGate):
        data['type'] =  'SX'
    elif isinstance(gate,QiskitSXdgGate):
        data['type'] =  'SXdg'
    
    #single-qubit, one parameter
    elif isinstance(gate,QiskitPhaseGate):
        data['type'] =  'Phase'
        data['params'] = gate.params
    elif isinstance(gate,QiskitRXGate):
        data['type'] =  'RX'
        data['params'] = gate.params
    elif isinstance(gate,QiskitRYGate):
        data['type'] =  'RY'
        data['params'] = gate.params
    elif isinstance(gate,QiskitRZGate):
        data['type'] =  'RZ'
        data['params'] = gate.params
    elif isinstance(gate,QiskitU1Gate):
        data['type'] =  'U1'
        data['params'] = gate.params
    
    #single-qubit, two- parameter
    elif isinstance(gate,QiskitRGate):
        data['type'] =  'R'
        data['params'] = gate.params
    elif isinstance(gate,QiskitU2Gate):
        data['type'] =  'U2'
        data['params'] = gate.params
    
    #single-qubit, three parameters
    elif isinstance(gate,QiskitUGate):
        data['type'] =  'U'
        data['params'] = gate.params
    elif isinstance(gate,QiskitU3Gate):
        data['type'] =  'U3'
        data['params'] = gate.params
    
   #two-qubit, no parameters 
    elif isinstance(gate,QiskitCHGate):
        data['type'] =  'CH'
    elif isinstance(gate,QiskitCXGate):
        data['type'] =  'CX'
    elif isinstance(gate,QiskitSwapGate):
        data['type'] =  'Swap'
    elif isinstance(gate,QiskitiSwapGate):
        data['type'] =  'iSwap'
    elif isinstance(gate,QiskitCSXGate):
        data['type'] =  'CSX'
    elif isinstance(gate,QiskitDCXGate):
        data['type'] =  'DCX'
    elif isinstance(gate,QiskitCYGate):
        data['type'] =  'CY'
    elif isinstance(gate,QiskitCZGate):
        data['type'] =  'CZ'
    
    #two-qubit, one parameter
    elif isinstance(gate,QiskitCPhaseGate):
        data['type'] =  'CPhase'
        data['params'] = gate.params
    elif isinstance(gate,QiskitCRXGate):
        data['type'] =  'CRX'
        data['params'] = gate.params
    elif isinstance(gate,QiskitRXXGate):
        data['type'] =  'RXX'
        data['params'] = gate.params
    elif isinstance(gate,QiskitCRYGate):
        data['type'] =  'CRY'
        data['params'] = gate.params
    elif isinstance(gate,QiskitRYYGate):
        data['type'] =  'RYY'
        data['params'] = gate.params
    elif isinstance(gate,QiskitCRZGate):
        data['type'] =  'CRZ'
        data['params'] = gate.params
    elif isinstance(gate,QiskitRZXGate):
        data['type'] =  'RZX'
        data['params'] = gate.params
    elif isinstance(gate,QiskitRZZGate):
        data['type'] =  'RZZ'
        data['params'] = gate.params
    elif isinstance(gate,QiskitCU1Gate):
        data['type'] =  'CU1'
        data['params'] = gate.params
    
    #two-qubit, two parameter
    
    
    #two-qubit, three parameter
    elif isinstance(gate,QiskitCU3Gate):
        data['type'] =  'CU3'
        data['params'] = gate.params
    
    #two-qubit, four parameter
    elif isinstance(gate,QiskitCUGate):
        data['type'] =  'CU'
        data['params'] = gate.params
    
    #multi-qubit gates
    elif isinstance(gate,QiskitCCXGate):
        data['type'] =  'CCX'
    elif isinstance(gate,QiskitRCCXGate):
        data['type'] =  'RCCX'
    elif isinstance(gate,QiskitRC3XGate):
        data['type'] =  'RC3X'
    elif isinstance(gate,QiskitCSwapGate):
        data['type'] =  'CSwap'
    elif isinstance(gate,QiskitMCPhaseGate):
        data['type'] =  'MCPhase'
    elif isinstance(gate,QiskitMCU1Gate):
        data['type'] =  'MCU1'
    
    #other
    elif isinstance(gate,QiskitMSGate):
        data['type'] = 'MS'
    
    #controlled
    elif isinstance(gate, QiskitControlledGate):
        data = get_qiskit_gate_data(gate.base_gate)
        data['num_controls'] = gate.num_ctrl_qubits
    
    #general unitary
    elif isinstance(gate, QiskitUnitaryGate):
        data['type'] = 'Unitary'
    
    #error    
    else:
        print("Cannot get gate data for the following gat type:", type(gate))

    return data


qiskit_gates = {
    'H': QiskitHGate,
    'X': QiskitXGate,
    'Y': QiskitYGate,
    'Z': QiskitZGate,
    'S': QiskitSGate,
    'Sdg': QiskitSdgGate,
    'T': QiskitTGate,
    'Tdg': QiskitTdgGate,
    'I': QiskitIGate,
    'SX': QiskitSXGate,
    'SXdg': QiskitSXdgGate,
    'Phase': QiskitPhaseGate,
    'RX': QiskitRXGate,
    'RY': QiskitRYGate,
    'RZ': QiskitRZGate,
    'U1': QiskitU1Gate,
    'R': QiskitRGate,
    'U2': QiskitU2Gate,
    'U': QiskitUGate,
    'U3': QiskitU3Gate,
    'CH': QiskitCHGate,
    'CX': QiskitCXGate,
    'Swap': QiskitSwapGate,
    'iSwap': QiskitiSwapGate,
    'CSX': QiskitCSXGate,
    'DCX': QiskitDCXGate,
    'CY': QiskitCYGate,
    'CZ': QiskitCZGate,
    'CPhase': QiskitCPhaseGate,
    'CRX': QiskitCRXGate,
    'RXX': QiskitRXXGate,
    'CRY': QiskitCRYGate,
    'RYY': QiskitRYYGate,
    'CRZ': QiskitCRZGate,
    'RZX': QiskitRZXGate,
    'RZZ': QiskitRZZGate,
    'CU1': QiskitCU1Gate,
    'RCCX': QiskitRCCXGate,
    'RC3X': QiskitRC3XGate,
    'CCX': QiskitCCXGate,
}

def create_qiskit_gate(data):
    
    gate_type = data['type']
    params = data['params']
    matrix = data['matrix']
    
    #measure
    if gate_type == 'MEASURE':
        return QiskitMeasurementGate()
    #single qubit gates
    elif gate_type in ('H','X','Y','Z','S','Sdg','T','Tdg','I','SX','SXdg'):
        return qiskit_gates[gate_type]()
    
    #single-qubit, one parameter
    elif gate_type in ('Phase','RX','RY','RZ','U1'):
        return qiskit_gates[gate_type](params[0])
    
    #single-qubit, two parameter
    if gate_type in ('R','U2'):
        return qiskit_gates[gate_type](params[0],params[1])
    
    #single-qubit, three parameter
    elif gate_type == 'U':
        return QiskitUGate()
    elif gate_type == 'U3':
        return QiskitU3Gate()
    
    #two-qubit, zero-parameter
    elif gate_type in ('CH', 'CX', 'Swap', 'iSwap', 'CSX', 'DCX', 'CY', 'CZ'):
        return qiskit_gates[gate_type]()
    
    #two-qubit, one-parameter
    elif gate_type in ('CPhase','CRX', 'RXX', 'CRY', 'RYY', 'CRZ', 'RZX', 'RZZ', 'CU1'):
        return qiskit_gates[gate_type](params[0])

    #two-qubit, two parameters
        
    
    #two-qubit, three parameters
    elif gate_type == 'CU3':
        return QiskitCU3Gate()
    
    #four parameters
    elif gate_type == 'CU':
        return QiskitCUGate()
    
    #multi-qubit gates
    elif gate_type == 'RCCX':
        return QiskitRCCXGate()
    elif gate_type == 'RC3X':
        return QiskitRC3XGate()
    elif gate_type == 'CCX':
        return QiskitCCXGate()
    elif gate_type == 'MCXGrayCode':
        return QiskitMCXGrayCodeGate()
    elif gate_type == 'MCXRecursive':
        return QiskitMCXRecursiveGate()
    elif gate_type == 'MCXVChain':
        return QiskitMCXVChainGate()
    elif gate_type == 'CSwap':
        return QiskitCSwapGate()
    
    #multi-qubit one-parameter
    elif gate_type == 'MCU1':
        return QiskitMCU1Gate()
    elif gate_type == 'MCPhase':
        return QiskitMCPhaseGate()
    
    #other
    elif gate_type == 'GMS':
        return QiskitMSGate()

    #non-compatible types, go from matrix
    elif not (matrix is None):
        return QiskitUnitaryGate(matrix, label=gate_type)

    #error
    else:
        print(matrix)
        print(gate_type)
        raise TypeError("Gate type not handled")
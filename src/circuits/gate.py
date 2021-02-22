from typing import Any, Sequence, Dict, Iterable, Union
import numpy as np

# TODO: include option to pass as scipy matrix
# import scipy as sp
import cirq

#aws imports
from braket.circuits.gate import Gate as BraketGate

#qiskit imports
from qiskit.circuit.gate import Gate as QiskitGate
from qiskit.circuit.controlledgate import ControlledGate as QiskitControlledGate

#cirq imports
from cirq.ops.gate_features import SingleQubitGate as CirqSingleQubitGate
from cirq.ops.gate_features import TwoQubitGate as CirqTwoQubitGate
from cirq.ops.gate_features import ThreeQubitGate as CirqThreeQubitGate

#types
CirqGate = Union[CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate]
CirqGateTypes = (CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate)
GateInputType = Union["BraketGate", 
                     "CirqSingleQubitGate", 
                     "CirqTwoQubitGate", 
                     "CirqThreeQubitGate",
                     "QiskitGate",
                     "QiskitControlledGate",
                     np.array]

#qiskit standard gates
from qiskit.circuit.library.standard_gates.h import HGate as QiskitHGate
from qiskit.circuit.library.standard_gates.h import CHGate as QiskitCHGate
from qiskit.circuit.library.standard_gates.x import CXGate as QiskitCXGate
from qiskit.circuit.library.standard_gates.i import IGate as QiskitIGate
from qiskit.circuit.library.generalized_gates.gms import MSGate as QiskitMSGate
from qiskit.circuit.library.standard_gates.p import PhaseGate as QiskitPhaseGate
from qiskit.circuit.library.standard_gates.p import CPhaseGate as QiskitCPhaseGate
from qiskit.circuit.library.standard_gates.p import MCPhaseGate as QiskitMCPhaseGate
from qiskit.circuit.library.standard_gates.r import RGate as QiskitRGate
from qiskit.circuit.library.standard_gates.x import RCCXGate as QiskitRCCXGate
from qiskit.circuit.library.standard_gates.x import RC3XGate as QiskitRC3XGate
from qiskit.circuit.library.standard_gates.rx import RXGate as QiskitRXGate
from qiskit.circuit.library.standard_gates.rx import CRXGate as QiskitCRXGate
from qiskit.circuit.library.standard_gates.rxx import RXXGate as QiskitRXXGate
from qiskit.circuit.library.standard_gates.ry import RYGate as QiskitRYGate
from qiskit.circuit.library.standard_gates.ry import CRYGate as QiskitCRYGate
from qiskit.circuit.library.standard_gates.ryy import RYYGate as QiskitRYYGate
from qiskit.circuit.library.standard_gates.rz import RZGate as QiskitRZGate
from qiskit.circuit.library.standard_gates.rz import CRZGate as QiskitCRZGate
from qiskit.circuit.library.standard_gates.rzx import RZXGate as QiskitRZXGate
from qiskit.circuit.library.standard_gates.rzz import RZZGate as QiskitRZZGate
from qiskit.circuit.library.standard_gates.s import SGate as QiskitSGate
from qiskit.circuit.library.standard_gates.s import SdgGate as QiskitSdgGate
from qiskit.circuit.library.standard_gates.swap import SwapGate as QiskitSwapGate
from qiskit.circuit.library.standard_gates.iswap import iSwapGate as QiskitiSwapGate
from qiskit.circuit.library.standard_gates.swap import CSwapGate as QiskitCSwapGate
from qiskit.circuit.library.standard_gates.sx import SXGate as QiskitSXGate
from qiskit.circuit.library.standard_gates.sx import SXdgGate as QiskitSXdgGate
from qiskit.circuit.library.standard_gates.sx import CSXGate as QiskitCSXGate
from qiskit.circuit.library.standard_gates.t import TGate as QiskitTGate
from qiskit.circuit.library.standard_gates.t import TdgGate as QiskitTdgGate
from qiskit.circuit.library.standard_gates.u import UGate as QiskitUGate
from qiskit.circuit.library.standard_gates.u import CUGate as QiskitCUGate
from qiskit.circuit.library.standard_gates.u1 import U1Gate as QiskitU1Gate
from qiskit.circuit.library.standard_gates.u1 import CU1Gate as QiskitCU1Gate
from qiskit.circuit.library.standard_gates.u1 import MCU1Gate as QiskitMCU1Gate
from qiskit.circuit.library.standard_gates.u2 import U2Gate as QiskitU2Gate
from qiskit.circuit.library.standard_gates.u3 import U3Gate as QiskitU3Gate
from qiskit.circuit.library.standard_gates.u3 import CU3Gate as QiskitCU3Gate
from qiskit.circuit.library.standard_gates.x import XGate as QiskitXGate
from qiskit.circuit.library.standard_gates.x import CXGate as QiskitCXGate
from qiskit.circuit.library.standard_gates.dcx import DCXGate as QiskitDCXGate
from qiskit.circuit.library.standard_gates.x import CCXGate as QiskitCCXGate
from qiskit.circuit.library.standard_gates.x import MCXGrayCode, MCXRecursive, MCXVChain
from qiskit.circuit.library.standard_gates.y import YGate as QiskitYGate
from qiskit.circuit.library.standard_gates.y import CYGate as QiskitCYGate
from qiskit.circuit.library.standard_gates.z import ZGate as QiskitZGate
from qiskit.circuit.library.standard_gates.z import CZGate as QiskitCZGate

#cirq standard gates
from cirq.ops.common_gates import (
    XPowGate as CirqXPowGate, 
    YPowGate as CirqYPowGate,
    ZPowGate as CirqZPowGate,
    HPowGate as CirqHPowGate,
    CZPowGate as CirqCZPowGate,
    CXPowGate as CirqCXPowGate
)
from cirq.ops.common_gates import (
    rx as cirq_rx,
    ry as cirq_ry,
    rz as cirq_rz,
    cphase as cirq_cphase
)
from cirq.ops.three_qubit_gates import (
    CCZPowGate as CirqCCZPowGate,
    CCXPowGate as CirqCCXPowGate,
    CSwapGate as CirqCSwapGate,
)

class Gate():
    
    """
    qBraid Gate class
    
    Args:
        gate: input object
        
    Attributes:
        name:
        num_qubits:
        matrix:
        _gate:
        _holding:
    
    Methods:
        to_qB:
    """
    
    def __init__(self, 
                 gate: GateInputType = None, 
                 name: str = None, 
                 gate_type:str = None ):
        
        self.gate = gate
        self.name = name
        
        self._gate_type = gate_type
        
        self.package = self._get_package_type()
        
        self._outputs = {}
    
    def _get_package_type(self,):
        
        assert self.gate
        
        if isinstance(self.gate, QiskitGate):
            return 'qiskit'
        elif isinstance(self.gate, CirqGateTypes):
            return 'cirq'
        else: return 'package not initialized'
    
    def gate_type(self):
    
        if not self._gate_type:
            self._gate_type = self._get_gate_type()
            
        return self._gate_type
        
    def _get_gate_type(self):
        
        if self.package =='qiskit':
        
            if isinstance(self.gate,QiskitHGate):
                return 'H'
            elif isinstance(self.gate,QiskitCHGate):
                return 'CH'
            elif isinstance(self.gate,QiskitCXGate):
                return 'CX'
            elif isinstance(self.gate,QiskitIGate):
                return 'I'
            elif isinstance(self.gate,QiskitMSGate):
                return 'MS'
            elif isinstance(self.gate,QiskitPhaseGate):
                return 'Phase'
            elif isinstance(self.gate,QiskitCPhaseGate):
                return 'CPhase'
            elif isinstance(self.gate,QiskitMCPhaseGate):
                return 'MCPhase'
            elif isinstance(self.gate,QiskitRGate):
                return 'RGate'
            elif isinstance(self.gate,QiskitRCCXGate):
                return 'RCCX'
            elif isinstance(self.gate,QiskitRC3XGate):
                return 'RC3X'
            elif isinstance(self.gate,QiskitRXGate):
                return 'RX'
            elif isinstance(self.gate,QiskitCRXGate):
                return 'CRX'
            elif isinstance(self.gate,QiskitRXXGate):
                return 'RXX'
            elif isinstance(self.gate,QiskitRYGate):
                return 'RY'
            elif isinstance(self.gate,QiskitCRYGate):
                return 'CRY'
            elif isinstance(self.gate,QiskitRYYGate):
                return 'RYY'
            elif isinstance(self.gate,QiskitRZGate):
                return 'RZ'
            elif isinstance(self.gate,QiskitCRZGate):
                return 'CRZ'
            elif isinstance(self.gate,QiskitRZXGate):
                return 'RZX'
            elif isinstance(self.gate,QiskitRZZGate):
                return 'RZZ'
            elif isinstance(self.gate,QiskitSGate):
                return 'S'
            elif isinstance(self.gate,QiskitSdgGate):
                return 'Sdg'
            elif isinstance(self.gate,QiskitSwapGate):
                return 'Swap'
            elif isinstance(self.gate,QiskitiSwapGate):
                return 'iSwap'
            elif isinstance(self.gate,QiskitCSwapGate):
                return 'CSwap'
            elif isinstance(self.gate,QiskitSXGate):
                return 'SX'
            elif isinstance(self.gate,QiskitSXdgGate):
                return 'SXdg'
            elif isinstance(self.gate,QiskitCSXGate):
                return 'CSX'
            elif isinstance(self.gate,QiskitTGate):
                return 'T'
            elif isinstance(self.gate,QiskitTdgGate):
                return 'Tdg'
            elif isinstance(self.gate,QiskitUGate):
                return 'U'
            elif isinstance(self.gate,QiskitCUGate):
                return 'CU'
            elif isinstance(self.gate,QiskitU1Gate):
                return 'U1'
            elif isinstance(self.gate,QiskitCU1Gate):
                return 'CU1'
            elif isinstance(self.gate,QiskitMCU1Gate):
                return 'MCU1'
            elif isinstance(self.gate,QiskitU2Gate):
                return 'U2'
            elif isinstance(self.gate,QiskitU3Gate):
                return 'U3'
            elif isinstance(self.gate,QiskitCU3Gate):
                return 'CU3'
            elif isinstance(self.gate,QiskitXGate):
                return 'X'
            elif isinstance(self.gate,QiskitCXGate):
                return 'CX'
            elif isinstance(self.gate,QiskitDCXGate):
                return 'DCX'
            elif isinstance(self.gate,QiskitCCXGate):
                return 'CCX'
            elif isinstance(self.gate,QiskitYGate):
                return 'Y'
            elif isinstance(self.gate,QiskitCYGate):
                return 'CY'
            elif isinstance(self.gate,QiskitZGate):
                return 'Z'
            elif isinstance(self.gate,QiskitCZGate):
                return 'CZ'
                
        elif self.package =='cirq':
            
            # single qubit gates
            if isinstance(self.gate, CirqHPowGate):
                if self.gate.exponent == 1:
                    return 'H'
                else:
                    pass
            if isinstance(self.gate, CirqXPowGate):
                if self.gate.exponent ==1:
                    return 'X'
                else:
                    pass
            if isinstance(self.gate, CirqYPowGate):
                if self.gate.exponent ==1:
                    return 'Y'
                else:
                    pass
            if isinstance(self.gate, CirqZPowGate):
                if self.gate.exponent ==1:
                    return 'Z'
                elif self.gate.exponent == 0.5:
                    return 'S'
                elif self.gate.exponent == 0.25:
                    return 'T'
                else:
                    pass
            #two qubit gates
            if isinstance(self.gate, CirqCXPowGate):
                if self.gate.exponent ==1:
                    return 'CX'
                else:
                    pass
            if isinstance(self.gate, CirqCZPowGate):
                if self.gate.exponent ==1:
                    return 'CZ'
                else:
                    pass
            #three qubit gates
            if isinstance(self.gate, CirqCCZPowGate):
                if self.gate.exponent == 1:
                    return 'CCZ'
                else:
                    pass
            if isinstance(self.gate, CirqCCXPowGate):
                if self.gate.exponent == 1:
                    return 'CCX'
                else:
                    pass
            if isinstance(self.gate, CirqCSwapGate):
                return 'CSwap'
            
    def _create_cirq_object(self):
        
        gate_type = self.gate_type()
        
        if gate_type == 'H':
            self._outputs['cirq'] = CirqHPowGate() #default exponent =1 
        elif gate_type == 'X':
            self._outputs['cirq'] = CirqXPowGate() #default exponent =1 
        elif gate_type == 'Y':
            self._outputs['cirq'] = CirqYPowGate() #default exponent =1 
        elif gate_type == 'Z':
            self._outputs['cirq'] = CirqZPowGate() #default exponent =1 
        elif gate_type == 'S':
            self._outputs['cirq'] = CirqZPowGate(exponent=0.5)
        elif gate_type == 'T':
            self._outputs['cirq'] = CirqZPowGate(exponent=0.25)
        elif gate_type =='CX':
            self._outputs['cirq'] = CirqCXPowGate() #default exponent = 1 
        
    
    def _create_qiskit_object(self):
        
        gate_type = self.gate_type()
        
        #single qubit gates
        if gate_type == 'H':
            self._outputs['qiskit'] = QiskitHGate()
        elif gate_type == 'X':
            self._outputs['qiskit'] = QiskitXGate()
        elif gate_type =='Y':
            self._outputs['qiskit'] = QiskitYGate()
        elif gate_type == 'Z':
            self._outputs['qiskit'] = QiskitZGate()
        elif gate_type == 'S':
            self._outputs['qiskit'] = QiskitSGate()
        elif gate_type == 'T':
            self._outputs['qiskit'] = QiskitTGate()
        #two qubit gates
        elif gate_type =='CX':
            self._outputs['qiskit'] = QiskitCXGate()
    
    def to_cirq(self):
        
        if 'cirq' not in self._outputs.keys():
            self._create_cirq_object()
        
        return self._outputs['cirq']
    
    def to_qiskit(self):
        
        if 'qiskit' not in self._outputs.keys():
            self._create_qiskit_object()
            
        return self._outputs['qiskit']


    
from typing import Any, Sequence, Dict, Iterable, Union
import numpy as np
from abc import ABC, abstractmethod
import abc


from .qiskit_gates import get_qiskit_gate_data, create_qiskit_gate, qiskit_gates
from .cirq_gates import get_cirq_gate_data, create_cirq_gate, cirq_gates
from .braket_gates import get_braket_gate_data, create_braket_gate
from .parameter import AbstractParameterWrapper

#aws imports
from braket.circuits.gate import Gate as BraketGate

#qiskit imports
from qiskit.circuit.gate import Gate as QiskitGate
from qiskit.circuit.controlledgate import ControlledGate as QiskitControlledGate
from qiskit.circuit import Parameter as QiskitParameter

#cirq imports
from cirq.ops.gate_features import SingleQubitGate as CirqSingleQubitGate
from cirq.ops.gate_features import TwoQubitGate as CirqTwoQubitGate
from cirq.ops.gate_features import ThreeQubitGate as CirqThreeQubitGate

#measurement gates
from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure
from qiskit.circuit.measure import Measure as QiskitMeasurementGate

#types
CirqGate = Union[CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate,CirqMeasure]
CirqGateTypes = (CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate,CirqMeasure)
QiskitGateTypes = (QiskitGate,QiskitControlledGate,QiskitMeasurementGate)
BraketGateTypes = (BraketGate)

GateInputType = Union["BraketGate", 
                     "CirqSingleQubitGate", 
                     "CirqTwoQubitGate", 
                     "CirqThreeQubitGate",
                     "QiskitGate",
                     "QiskitControlledGate",
                     np.array]

class AbstractGate(ABC):
    
    def __init__(self):
        
        self.gate = None
        self.name = None
        self.package = None
        
        self.params = None
        self.matrix = None
        
        self.num_controls = 0
        self.base_gate = None
        
        self._gate_type = None
        self._outputs = {}
    
# =============================================================================
#     def get_data(self):
#         
#         data = {'name':self.name,
#                 'type': self._gate_type,
#                 'package': self.package,
#                 'params': self.params,
#                 'matrix': self.matrix,
#                 }
#         if self.base_gate:
#             data['num_controls'] = self.num_controls
#             data['base_gate'] = self.base_gate
# =============================================================================
    
    def transpile(self, package: str):
        
        if not package in self._outputs.keys():
            self._create_output(package)
        return self._outputs[package]

    def _create_output(self, package: str):
        
        if package == 'qiskit':
            self._create_qiskit()
        elif package == 'braket':
            self._create_braket()
        elif package == 'cirq':
            self._create_cirq()
        else:
            print("package not yet handled")
            
    def _create_qiskit(self):    
        
        qiskit_params = self.params.copy()
        for i, param in enumerate(qiskit_params):
            if isinstance(param,AbstractParameterWrapper):
                qiskit_params[i] = param.transpile('cirq')
        
        
        data = {'type': self._gate_type,
                    'matrix': self.matrix,
                    'name':self.name,
                    'params':qiskit_params}
        
        if self._gate_type in qiskit_gates.keys():
            
            self._outputs['qiskit'] = create_qiskit_gate(data)
        
        elif self.base_gate:
            self._outputs['qiskit'] = self.base_gate.transpile('qiskit').control(self.num_controls)
        
        elif not (self.matrix is None):
            data['type'] = 'Unitary'
            self._outputs['qiskit'] = create_qiskit_gate(data)
        
    def _create_cirq(self):
        
        cirq_params = self.params.copy()
        for i, param in enumerate(cirq_params):
            if isinstance(param,AbstractParameterWrapper):
                cirq_params[i] = param.transpile('cirq')
        
        data = {'type': self._gate_type,
                    'matrix': self.matrix,
                    'name':self.name,
                    'params':cirq_params}
        
        if self._gate_type in cirq_gates.keys():
            self._outputs['cirq'] = create_cirq_gate(data)
        
        elif self.base_gate:
            self._outputs['cirq'] = self.base_gate.transpile('cirq').controlled(self.num_controls)

        elif not (self.matrix is None):
            data['name'] = data['type']
            data['type'] = 'Unitary'
            self._outputs['cirq'] = create_cirq_gate(data)
    
    def _create_braket(self):
        
        self._outputs['braket'] = create_braket_gate(self._gate_type, self.params)
    
        
class QiskitGateWrapper(AbstractGate):
    
    def __init__(self, gate: QiskitGate, params: QiskitParameter = None):
        
        super().__init__()
        
        self.gate = gate
        self.params = params
        self.name = gate.name
        
        data = get_qiskit_gate_data(gate)
        
        self.matrix = data['matrix']
        #self.params = data['params']
        self.num_controls = data['num_controls']
        
        self._gate_type = data['type']
        self._outputs['qiskit'] = gate
        self.package = 'qiskit'


class BraketGateWrapper(AbstractGate):
    
    def __init__(self, gate: BraketGate):
        
        super().__init__()
        
        self.gate = gate
        self.name = None
        
        data = get_braket_gate_data(gate)
        
        self.matrix = data['matrix']
        self.params = data['params']
        
        if 'base_gate' in data.keys():
            self.base_gate = BraketGateWrapper(data['base_gate'])
            #self.base_gate = data['base_gate']
            self.num_controls = data['num_controls']
        
        self._gate_type = data['type']
        self._outputs['braket'] = gate
        self.package = 'braket'
        
    
class CirqGateWrapper(AbstractGate):
    
    def __init__(self, gate: CirqGate):
        
        super().__init__()
        
        self.gate = gate
        self.name = None
        
        data = get_cirq_gate_data(gate)
        
        self.matrix = data['matrix']
        self.params = data['params']
        self.num_controls = data['num_controls']
        
        self._gate_type = data['type']
        self._outputs['cirq'] = gate
        self.package = 'cirq'
    
class QbraidGateWrapper(AbstractGate):
    
    def __init__(self, gate_type: str):
        
        super().__init__()
        
        self._gate_type = gate_type
        self.package = 'qbraid'
    
    """
    qBraid Gate Wrapper class
    
    Args:
        gate: input object
        name (optional): name of the gate
        gate_type: a string demonstrating the gate type according to qBraid
            documentation. (eg. 'H', 'CX', 'MEASURE')
        
    Attributes:
        package: the name of the pacakge to which the original gate object
            belongs (eg. 'qiskit')
    
    Methods:
        
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
    
    def _get_package_type(self):
        
        if self.gate:
            if isinstance(self.gate, QiskitGateTypes):
                return 'qiskit'
            elif isinstance(self.gate, CirqGateTypes):
                return 'cirq'
            elif isinstance(self.gate, BraketGateTypes):
                return 'braket'
            else:
                print('could not detect the package for this gate')
                print(type(self.gate))
        else: 
            return None
    
    def gate_type(self):
    
        if not self._gate_type:
            self._gate_type = self._get_gate_type()
            
        return self._gate_type
        
    def _get_gate_type(self):
        
        if self.package =='qiskit':
        
            #measurement
            if isinstance(self.gate,QiskitMeasurementGate):
                return 'MEASURE'
            
            #single-qubit gates
            elif isinstance(self.gate,QiskitHGate):
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
                self.params = self.gate.params
                return 'RX'
            elif isinstance(self.gate,QiskitCRXGate):
                return 'CRX'
            elif isinstance(self.gate,QiskitRXXGate):
                return 'RXX'
            elif isinstance(self.gate,QiskitRYGate):
                self.params = self.gate.params
                return 'RY'
            elif isinstance(self.gate,QiskitCRYGate):
                return 'CRY'
            elif isinstance(self.gate,QiskitRYYGate):
                return 'RYY'
            elif isinstance(self.gate,QiskitRZGate):
                self.params = self.gate.params
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
            else:
                print("Type Not Handled")
                
        elif self.package =='cirq':
            
            # measurement gate
            if isinstance(self.gate,CirqMeasure):
                #add info self.measurement_map
                return 'MEASURE'
            
            # single qubit gates
            if isinstance(self.gate, CirqHPowGate):
                if self.gate.exponent == 1:
                    return 'H'
                else:
                    pass
            if isinstance(self.gate, CirqXPowGate):
                if self.gate.exponent ==1:
                    return 'X'
                elif self.gate.global_shift== -0.5:
                    self.params = [self.gate.exponent*np.pi]
                    return 'RX'
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
            else:
                raise TypeError("Could not determined gate type.")
            
        elif self.package == 'braket':
            
            #single qubit gates
            if isinstance(self.gate, BraketGate.H):
                return 'H'
            elif isinstance(self.gate, BraketGate.X):
                return 'X'
            elif isinstance(self.gate, BraketGate.Y):
                return 'Y'
            elif isinstance(self.gate, BraketGate.Z):
                return 'Z'
            elif isinstance(self.gate, BraketGate.S):
                return 'S'
            elif isinstance(self.gate, BraketGate.T):
                return 'T'

            #multi-qubit gates
            elif isinstance(self.gate,BraketGate.CNot):
                return 'CX'
            #error
            else:
                print(self.package)
                print(self.gate)
                raise TypeError("Could not determine gate type.")
            
    def _create_cirq_object(self):
        
        """
        Creates a cirq gate object of the corresponding gate_type, 
        eg. HPowGate(), or CirqCXPowGate(), and stores it in the _outputs
        attribute.
        
        If the gate type is 'MEASURE', returns the string 'CirqMeasure',
            because the CirqMeasure gate cannot be instantiated as a gate.
        """
        
        gate_type = self.gate_type()
        
        #single-qubit, no parameters
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
        
        # single-qubit, one-parameter gates
        elif gate_type == 'RX':
            self._outputs['cirq'] = cirq_rx(self.params[0])
            
        #two-qubit, no parameters
        elif gate_type =='CX':
            self._outputs['cirq'] = CirqCXPowGate() #default exponent = 1 
            
        elif gate_type == 'MEASURE':
            self._outputs['cirq'] = 'CirqMeasure'
        #error
        else:
            print(gate_type)
            raise TypeError("Gate type not handled")
    
    def _create_qiskit_object(self):
        
        """
        Creates a qiskit gate object of the corresponding `gate_type`, and
        stores it in the `_outputs` attribute.
        """
        
        gate_type = self.gate_type()
        
        #measure
        if gate_type == 'MEASURE':
            self._outputs['qiskit'] = QiskitMeasurementGate()
        #single qubit gates
        elif gate_type == 'H':
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
        elif gate_type =='RX':
            self._outputs['qiskit'] = QiskitRXGate(self.params) 
        #two qubit gates
        elif gate_type =='CX':
            self._outputs['qiskit'] = QiskitCXGate()
        #error
        else:
            print(gate_type)
            raise TypeError("Gate type not handled")
    
    def _create_braket_object(self):
        
        
        """
        Creates a braket gate object of the corresponding gate_type, 
        eg. Gate.H(), or Gate.T(), and stores it in the _outputs
        attribute.
        
        If the gate type is 'MEASURE', returns the string 'BraketMeasure',
            because the BraketMeasure gate cannot be instantiated as a gate.
        """
        
        gate_type = self.gate_type()
        
        #single qubit 
        if gate_type == 'H':
            self._outputs['braket'] = BraketGate.H()
        elif gate_type == 'I':
            self._outputs['braket'] = BraketGate.I()
        elif gate_type == 'S':
            self._outputs['braket'] = BraketGate.S()
        elif gate_type == 'T':
            self._outputs['braket'] = BraketGate.T()
        elif gate_type == 'V':
            self._outputs['braket'] = BraketGate.V()
        elif gate_type == 'X':
            self._outputs['braket'] = BraketGate.X()
        elif gate_type == 'Y':
            self._outputs['braket'] = BraketGate.Y()
        elif gate_type == 'Z':
            self._outputs['braket'] = BraketGate.Z()
        elif gate_type =='RX':
            self._outputs['braket'] = BraketGate.Rx(self.params[0])
        
        #multi qubit gates
        elif gate_type == 'CX':
            self._outputs['braket'] = BraketGate.CNot()
        elif gate_type == 'CCX':
            self._outputs['braket'] = BraketGate.CCNot()
        elif gate_type == 'CPhase':
            pass
            #choice of CPhaseShift, CPhaseShift00, CPhaseShift01, CPhaseShift10
            #self._oututs['braket'] = BraketGate.CPhaseShift()
        elif gate_type == 'Swap':
            self._outputs['braket'] = BraketGate.Swap()
        elif gate_type == 'iSwap':
            self._outputs['braket'] = BraketGate.ISwap()
        elif gate_type == 'PSwap':
            pass
        elif gate_type == 'XX':
            self._outputs['braket'] = BraketGate.XX()
        elif gate_type == 'XY':
            self._outputs['braket'] = BraketGate.XY()
        elif gate_type == 'YY':
            self._outputs['braket'] = BraketGate.YY()
        elif gate_type =='ZZ':
            self._outputs['braket'] = BraketGate.ZZ()
            
        # measure
        elif gate_type == 'MEASURE':
            self._outputs['braket'] = 'BraketMeasure'
        # error
        else:
            print(gate_type)
            raise TypeError("Gate type not handled")
        
    def _to_cirq(self):
        
        """
        If the object has not already been transpiled to its cirq equivalent,
        do so, store it under the _objects attribute, and return the object.
        """
        
        if 'cirq' not in self._outputs.keys():
            self._create_cirq_object()
        
        return self._outputs['cirq']
    
    def _to_qiskit(self):
        
        """
        If the object has not already been transpiled to its qiskit equivalent,
        do so, store it under the _objects attribute, and return the object.
        """
        
        if 'qiskit' not in self._outputs.keys():
            self._create_qiskit_object()
            
        return self._outputs['qiskit']
    
    def _to_braket(self):
        
        """
        If the object has not already been transpiled to its braket equivalent,
        do so, store it under the _objects attribute, and return the object.
        """
        
        if 'braket' not in self._outputs.keys():
            self._create_braket_object()
            
        return self._outputs['braket']
    
    def output(self, package: str):
        
        """
        Transpiles the object to its equivalent in another package.
        
        Args:
            package: the package of the desired output object.
        """
        
        if package == 'qiskit':
            return self._to_qiskit()
        elif package == 'cirq':
            return self._to_cirq()
        elif package == 'braket':
            return self._to_braket()

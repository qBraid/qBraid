from typing import Any, Sequence, Dict, Iterable, Union
import numpy as np
from abc import ABC, abstractmethod
import abc


from .qiskit.utils import get_qiskit_gate_data, create_qiskit_gate, qiskit_gates
from .cirq.utils import get_cirq_gate_data, create_cirq_gate, cirq_gates
from .braket.utils import get_braket_gate_data, create_braket_gate
from .parameter import AbstractParameterWrapper

#braket imports
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
                qiskit_params[i] = param.transpile('qiskit')
        
        
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
        
        if self._gate_type in cirq_gates.keys  ():
            self._outputs['cirq'] = create_cirq_gate(data)
        
        elif self.base_gate:
            self._outputs['cirq'] = self.base_gate.transpile('cirq').controlled(self.num_controls)

        elif not (self.matrix is None):
            data['name'] = data['type']
            data['type'] = 'Unitary'
            self._outputs['cirq'] = create_cirq_gate(data)
    
    def _create_braket(self):
        
        self._outputs['braket'] = create_braket_gate(self._gate_type, self.params)
    
        
    

    


from ..gate import AbstractGate
from .utils import get_qiskit_gate_data

from qiskit.circuit.gate import Gate as QiskitGate
from qiskit.circuit.controlledgate import ControlledGate as QiskitControlledGate
from qiskit.circuit import Parameter as QiskitParameter


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

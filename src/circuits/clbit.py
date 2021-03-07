from typing import Any, Sequence, Dict, Iterable, Union

from qiskit.circuit.classicalregister import Clbit as QiskitClbit
from qiskit.circuit.classicalregister import ClassicalRegister as QiskitClassicalRegister

clbitInput = Union["QiskitClbit", int, str]  

class Clbit():
    
    """
    Clbit Class: hold clbit objects
    
    Args:
        clbit: input object, acceptable objects include:
            Braket, qiskit, cirq
    """
    
    def __init__(self, clbit: clbitInput = None):
        
        self.clbit = clbit
        
        if isinstance(clbit, QiskitClbit):
            self.index = clbit.index
        elif isinstance(clbit, [int]):
            self.index = clbit
        else:
            print("{} not implemented for Clbit".format(type(clbit)))
        
        self._outputs = {}
        
        
    def _create_cirq_object(self):
        
        self.outputs['cirq'] = self.index
        
        
    def _create_qiskit_object(self, register: QiskitClassicalRegister, index: int):
        
        self.outputs['qiskit'] = QiskitClbit(register, index)
        
    def _create_braket_object(self):
        
        self.outputs['braket'] = self.index
        
    def _output_to_cirq(self):
        
        if 'cirq' not in self.outputs.keys() or not self.outputs['cirq']:
            self._create_cirq_object()
        
        return self.outputs['cirq']
        
    def _output_to_qiskit(self):
        
        try:
            return self.outputs['qiskit']
        except:
            print("qiskit output not initialized in clbit {}".format(self.index))
            
    def _output_to_braket(self):
        
        if 'braket' not in self.outputs.keys() or not self.outputs['braket']:
            self._create_braket_object()
        
        return self.outputs['braket']
    
    def output(self, package: str):
        
        if package == 'qiskit':
            return self._output_to_cirq()
        elif package == 'cirq':
            return self._output_to_cirq()
        elif package == 'braket':
            return self._output_to_braket()
        else:
            print("Output of clbit not implemented for this package: {}".format(package))
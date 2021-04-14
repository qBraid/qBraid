from typing import Union
from sympy import Symbol
from qiskit.circuit import Parameter as QiskitParameter

ParameterInput = Union[float,int]

class AbstractParameterWrapper():
    
    def __init__(self):
    
        self.name = None
        self.parameter = None

        self._outputs = {}

    def _create_cirq(self):
        
        self._outputs['cirq'] = Symbol(self.name)
        
    def _create_qiskit(self):
        
        self._outputs['qiskit'] = QiskitParameter(self.name)
        
    def transpile():
        pass
    
class CirqParameterWrapper(AbstractParameterWrapper):
    
    def __init__(self, parameter: Symbol):
        
        super().__init__()
        
        self.name = parameter.name
        self.parameter = parameter
        
    def transpile(self, package: str):
        
        if package == 'cirq':
            return self.parameter
        elif package == 'qiskit':
            if not 'qiskit' in self._outputs.keys():
                self._create_qiskit()
            return self._outputs['qiskit']
        else:
            print("Package not supported.")
        
class QiskitParameterWrapper(AbstractParameterWrapper):
    
    def __init__(self, parameter: QiskitParameter):
        
        super().__init__()
        
        self.name = parameter.name
        self.parameter = parameter
        
        
    def transpile(self, package: str):
        
        if package == 'qiskit':
            return self.parameter
        elif package == 'cirq':
            if not 'cirq' in self._outputs.keys():
                self._create_cirq()
            return self._outputs['cirq']
        else:
            print("Package not supported")
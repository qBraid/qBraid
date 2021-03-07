from typing import Union

from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure
from qiskit.circuit.measure import Measure as QiskitMeasure


MeasureInput = Union['CirqMeasure','QiskitMeasure']

class Measure():
    
    def __init__(self,measure:MeasureInput):
        
        self.measure = measure
        
    def
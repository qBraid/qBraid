from typing import Any, Sequence, Dict, Iterable, Union

####################################

from circuits.instruction import qB_Instruction
from circuits.moment import qB_Moment

from braket.circuits.circuit import Circuit as aws_Circuit

from cirq.circuits import Circuit as cirq_Circuit

#####################################

qB_CircuitInput = Union["aws_Circuit", "cirq_Circuit", Iterable[qB_Moment], Iterable[qB_Instruction]]

class qB_Circuit():
    def __init__(self, circuit: qB_CircuitInput = None):
        
        self._holding = True
        if type(circuit) == Iterable[qB_Instruction]:
            self._holding = False
            moment_list = []
            for i in range(len(circuit)):
                moment_list.append(qB_Moment(circuit[i], i))
            circuit = moment_list
        
        if type(circuit) == Iterable[qB_Moment]:
            self._holding = False
            self.moment_set = circuit
            
            self._circuit = self
        
        if self._holding:
            self._circuit = circuit
            
    def __str__(self):
        if self._holding:
            return str(self._circuit)
        return str([str(moment) for moment in self.moment_set])
        
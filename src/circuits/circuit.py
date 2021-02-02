from typing import Any, Sequence, Dict, Iterable, Union

####################################

from circuits.instruction import qB_Instruction
from circuits.moment import qB_Moment

from braket.circuits.circuit import Circuit as aws_Circuit
from qiskit.circuit import QuantumCircuit as qiskit_Circuit
from cirq.circuits import Circuit as cirq_Circuit


#####################################

#types 
qB_CircuitInput = Union["aws_Circuit", "cirq_Circuit", "qiskit_Circuit", 
                        Iterable[qB_Moment], Iterable[qB_Instruction]]

class QbraidCircuit():
    
    """
        Create a QbraidCircuit object.
        
        Either a list of lower level operations (instructions or moments) that
        function as a circuit or a holder class for any of the following 
        types of of circuits:
            cirq: Circuit
            aws: Circuit
            qiskit: QuantumCircuit
            
        Args:
            circuit: the circuit object
        
        Attributes:
            _holding: determines whether the class is a holding class
            moment_set: a list of qB_Moment objects
            _circuit: the circuit object
        
        Raises:
            typeError: if the circuit object is not a supported type
            
        Examples:
     """       
    
    def __init__(self, circuit: qB_CircuitInput = None):
        
        """
        If object passed is an iterable, convert to a list of moments
        """
        
        #determine whether this stores a list of child objects or a holder
        self._holding = True 
        
        #if the object passed is and iterable of instructions,
        if type(circuit) == Iterable[qB_Instruction]:
            
            """
            moment_list = []
            for i in range(len(circuit)):
                moment_list.append(qB_Moment(circuit[i], i))
            """
            circuit = [qB_Moment(x,index) for index, x in circuit]
        
        #if circuit is a list of moments, store in moment_set attribute
        if type(circuit) == Iterable[qB_Moment]:
            self._holding = False
            self.moment_set = circuit
            
            self._circuit = self   # I'm confused?
        
        #if circuit is not an iterable of lower objects, store circuit object
        elif self._holding:
            self._circuit = circuit
        
            
    def __str__(self):
        if self._holding:
            return str(self._circuit)
        return str([str(moment) for moment in self.moment_set])
        
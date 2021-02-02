from typing import Any, Sequence, Dict, Iterable, Union

#############################

from braket.circuits.qubit import Qubit as aws_Qubit
from qiskit.circuit.quantumregister import Qubit as qiskit_Qubit
from cirq.ops.named_qubit import NamedQubit as cirq_NamedQubit

#############################

qB_QubitInput = Union["aws_Qubit", "cirq_NamedQubit","qiskit_Qubit", int, str]  

class qB_Qubit():
    
    """
    A holder instance of qB_Qubit has one property: self._qubit, which returns the original aws_Qubit, etc. object passed for it to hold.
    
    A definitive instance of qB_Qubit is made from passing an int or str name to define the qubit. In this case self._qubit is the identity.
    
    To get from a holder instance to definitive instance, the to_qB() method grabs the necessary data that defines the definitive instance
        from the held aws_Qubit, etc. object and modifies the instance in place by redefinition.
    """
    
    def __init__(self, qubit: qB_QubitInput = None):
        
        self._holding = True
        if type(qubit) == int or type(qubit) == str:
            self._holding = False
            self.name = qubit
            
            self._qubit = self
            
        if self._holding:
            self._qubit = qubit
        
        
    def __str__(self):
        if self._holding:
            return str(self._qubit)
        return 'qB_Qubit({})'.format(self.name)
    
    def __int__(self):
        if self._holding:
            return int(self._qubit) #are we sure this works for all types of qubits?
        return int(self.name)
    
    #################################################
    
    def to_qB(self):
        if type(self._qubit) != qB_Qubit:
            try:
                qubit_name = int(self)
            except:
                qubit_name = str(self)
            
            return qB_Qubit(qubit_name)
            
    #################################################
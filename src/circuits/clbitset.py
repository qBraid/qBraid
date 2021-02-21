# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 16:14:04 2021

@author: Erik
"""

from typing import Any, Sequence, Dict, Iterable, Union

from clbit import Clbit

#from braket.circuits.qubit_set import QubitSet as aws_QubitSet
from qiskit.circuit.classicalregister import ClassicalRegister as QiskitClassicalRegister
#from cirq.ops.qubit_order import QubitOrder as cirq_QubitOrder


ClbitSetInput = Union["aws_QubitSet", "cirq_QubitOrder","qiskit_QuantumRegister", Iterable[Clbit], Iterable[str], Iterable[int]]  

class ClbitSet():
    
    """
    A holder instance of ClbitSet
    
    Arguments:
        A definitive instance of ClbitSet is made by passing an iterable
        of the int or str names to define the clbits.
        
    Attributes:

    Methods:


    """
    
    def __init__(self, clbitset: ClbitSetInput = None):
        
        if clbitset:
            self.clbits = [Clbit(clbit) for clbit in clbitset]
        else: 
            self.clbits = []
        
    def __len__(self):
        return len(self.clbits)
        
    def get_qubit_by_id(self, id):
        pass
    
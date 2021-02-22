from typing import Any, Sequence, Dict, Iterable, Union

from qiskit.circuit.classicalregister import Clbit as QiskitClbit


clbitInput = Union["Qiskitclbit", int, str]  

class Clbit():
    
    """
    Clbit Class: hold clbit objects
    
    Args:
        clbit: input object, acceptable objects include:
            Braket, qiskit, cirq
    """
    
    def __init__(self, clbit: clbitInput = None):
        
        self.clbit = clbit
        

from typing import Any, Sequence, Dict, Iterable, Union
import numpy as np

# TODO: include option to pass as scipy matrix
# import scipy as sp

##########################

from braket.circuits.gate import Gate as aws_Gate

from cirq.ops.gate_features import SingleQubitGate as cirq_SingleQubitGate
from cirq.ops.gate_features import TwoQubitGate as cirq_TwoQubitGate
from cirq.ops.gate_features import ThreeQubitGate as cirq_ThreeQubitGate

##########################

qB_GateInput = Union["aws_Gate", "cirq_SingleQubitGate", "cirq_TwoQubitGate", "cirq_ThreeQubitGate", np.array]

class qB_Gate():
    def __init__(self, gate: qB_GateInput = None, name: str = None):
        
        self._holding = True
        if type(gate) == np.array:
            self._holding = False
            if name == None:
                print("Error: please pass a name for this gate")
                raise # TODO: implement error
            
            s = np.shape(gate)
            if len(s) != 2 or s[0] != s[1]:
                print("Error: please pass a square numpy array to define gate")
                raise # TODO: implement error
            n_qubits = s[0]
            
            self.name = name
            self.num_qubits = n_qubits
            self.matrix = gate
            
            self._gate = self
            
        if self._holding:    
            self._gate = gate
            
    def __str__(self):
        if self._holding:
            return str(self._gate)
        return self.name + ': ' + str(self.matrix)
    
    
    #############################################
    
    def to_qB(self):
        if type(self._gate) != qB_Gate:
            pass
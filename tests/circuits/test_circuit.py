# -*- coding: utf-8 -*-
# All rights reserved-2019©.
import numpy as np


## SET BACKEND
import matplotlib as mpl
mpl.use("TkAgg")


from qbraid.circuits.circuit import Circuit
from qbraid.circuits.moment import Moment
from qbraid.circuits.instruction import Instruction

def test_creating_circuit():
    circuit = Circuit(num_qubits=3,name="test_circuit")
    print(circuit)
    
test_creating_circuit()
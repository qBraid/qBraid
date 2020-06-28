# -*- coding: utf-8 -*-
# All rights reserved-2019©. 
import unittest
import numpy as np
from pyquil import quil, Program, gates
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit.measure import Measure
from cirq import Circuit
from qBraid.conversions.q_circ_conversion import *

from pyquil import quil
from pyquil import Program
from pyquil.gates import *
from pyquil import gates


class convert_q_circ__test(unittest.TestCase):

    def test_q_circ_convert(self):
        pass

    def test_initialize_qiskit_circuit(self):
        cr = {'ro': [0, 1, 2], 'ro3': [0, 1], 'ro1': [0, 1, 2], 'ro2': [0]}
        [qr, cr_list, qiskit_circ] = initialize_qiskit_circuit(4,cr)
        self.assertTrue(1 == 1)

    def test_pyquil_circ_conversion(self):
        p = Program()
        p.inst(H(0)) # A single instruction
        # p += CNOT(0, 1)
        # p += CNOT(1, 2)
        p += CNOT(3, 4)
        p.inst(RX(np.pi/2, 2), Y(1)) # Multiple instructions
        p.inst(RY(np.pi/2, 2), Y(1)) # Multiple instructions
        p.inst(RZ(np.pi/2, 2), Y(1)) # Multiple instructions
        p.inst([H(0), Z(1)]) # A list of instructions
        p.inst(H(i) for i in range(4)) # A generator of instructions
        p.inst(("H", 1)) # A tuple representing an instruction
        p.inst("X 3") # A string representing an instruction
        # q = Program()
        # p.inst(q) # Another program
        ro = p.declare('ro', 'BIT', 3)
        ro2 = p.declare('ro2', 'BIT', 3)
        ro3 = p.declare('ro3', 'BIT', 3)
        ro1 = p.declare('ro1', 'BIT', 3)

        p += X(0)
        p += MEASURE(0, ro[0])
        p += MEASURE(1, ro[1])
        p += MEASURE(2, ro[2])
        # ro1 = p.declare('ro1', 'BIT', 1)
        p += MEASURE(3, ro3[0])
        
        p += MEASURE(0, ro1[0])
        p += MEASURE(1, ro1[1])
        p += MEASURE(2, ro1[2])
        p += MEASURE(0, ro2[0])
        p += MEASURE(1, ro3[1])
        p += MEASURE(2, ro[2])
        ret_circ=pyquil_circ_conversion(p)
        print('\n')
        print(ret_circ)





if __name__=='__main__':
    unittest.main()
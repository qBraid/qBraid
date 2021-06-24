# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from qbraid.circuits.circuit import Circuit
from qbraid.circuits.moment import Moment
from qbraid.circuits.instruction import Instruction
from qbraid.circuits.gate import TestGate

circ = Circuit(3)
circ.append(Moment(TestGate()([0,1])))

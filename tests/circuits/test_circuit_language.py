# -*- coding: utf-8 -*-
# All rights reserved-2021©.


import numpy as np
import pytest

from qbraid import circuits
from qbraid.circuits.library.standard_gates.h import CH


"""
GATE TESTS
"""
def test_single_qubit():
    h  = circuits.H(global_phase=10)
    assert h.global_phase == 10

def test_h_control():
    h  = circuits.H(global_phase=10)
    assert type(h.control()) == CH

def test_two_qubit():
    ch  = circuits.CH(global_phase=10)
    assert ch.num_qubits == 2

def test_u3():
    u3 = circuits.U3(theta=0.3,phi=3,lam=10.0)
    assert u3.params == [0.3,3,10.0]
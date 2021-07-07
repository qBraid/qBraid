# -*- coding: utf-8 -*-
# All rights reserved-2021©.


import numpy as np
#import pytest

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

from qbraid.circuits import *

def create_gates():
    h = H().control(1)
    dcx = DCX().control(1)
    ch = CH().control(1)
    ch = HPow(exponent =1.5).control(1)
    i = I().control(1)
    iswap = iSwap().control(1)
    p = Phase(1.1).control(1)
    cphase = CPhase(3.2).control(1)
    pswap = pSwap().control(1)
    r = R(1,2).control(1)
    rx = RX(2).control(1)
    rxx = RXX(3).control(1)
    rxy = RXY(1.2).control(1)
    ry = RY(3).control(1)
    ryy = RYY(1.2).control(1)
    rz = RZ(1.45).control(1)
    rzz = RZZ(3.1).control(1)
    rzx = RZX(1.2).control(1)
    s = S().control(1)
    sdg = Sdg().control(1)
    swap = Swap().control(1)
    sx = SX().control(1)
    sxdg = SXdg().control(1)
    t = T().control(1)
    tdg = Tdg().control(1)
    u = U(1,2,3).control(1)
    u1 = U1(1).control(3)
    u2 = U2(1,1.1).control(1)
    u3 = U3(3,3,3).control(1)
    x = X().control(1)
    cx = CX().control(1)
    xpow = XPow(3).control(1)
    y = Y().control(1)
    cy = CY().control(1)
    ypow = YPow().control(1)
    cz = CZ().control(1)
    z = Z().control(1)
    zpow = ZPow().control(1)

def assemble_circuit():
    circ = Circuit(5)
    h= H()
    cnot = CX()
    circ.append([h(i) for i in range(5)])
    circ.append([not([i,i+1]) for i in range(4)])

if __name__=="__main__":

    create_gates()

    assemble_circuit()
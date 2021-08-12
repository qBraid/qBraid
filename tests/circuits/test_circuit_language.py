# -*- coding: utf-8 -*-
# All rights reserved-2021©.


import pytest

from qbraid.circuits.controlledgate import ControlledGate
from qbraid import circuits
from qbraid.circuits import *

"""
GATE TESTS
"""


class TestGate:

    def test_single_qubit(self):
        """Tests single qubit gate."""
        h = circuits.H(global_phase=10)
        assert h.global_phase == 10

    def test_h_control(self):
        """Tests H control gate."""
        h = circuits.H(global_phase=10)
        assert type(h.control()) == CH

    def test_two_qubit(self):
        """Tests two qubit gate.
        """
        ch = circuits.CH(global_phase=10)
        assert ch.num_qubits == 2

    def test_u3(self):
        """Tests U3 gate params.
        """
        u3 = circuits.U3(theta=0.3, phi=3, lam=10.0)
        assert u3.params == [0.3, 3, 10.0]

    def test_create_control_gates(self):
        """Tests creating control gates.
        """
        gate_list = []
        gate_list.append(H(2).control(1))
        gate_list.append(DCX().control(1))
        gate_list.append(CH().control(1))
        gate_list.append(HPow(exponent=1.5).control(1))
        gate_list.append(I().control(1))
        gate_list.append(iSwap().control(1))
        gate_list.append(Phase(1.1).control(1))
        gate_list.append(CPhase(3.2).control(1))
        gate_list.append(pSwap().control(1))
        gate_list.append(R(1, 2).control(1))
        gate_list.append(RX(2).control(1))
        gate_list.append(RXX(3).control(1))
        gate_list.append(RXY(1.2).control(1))
        gate_list.append(RY(3).control(1))
        gate_list.append(RYY(1.2).control(1))
        gate_list.append(RZ(1.45).control(1))
        gate_list.append(RZZ(3.1).control(1))
        gate_list.append(RZX(1.2).control(1))
        gate_list.append(S().control(1))
        gate_list.append(Sdg().control(1))
        gate_list.append(Swap().control(1))
        gate_list.append(SX().control(1))
        gate_list.append(SXdg().control(1))
        gate_list.append(T().control(1))
        gate_list.append(Tdg().control(1))
        gate_list.append(U(1, 2, 3).control(1))
        gate_list.append(U1(1).control(3))
        gate_list.append(U2(1, 1.1).control(1))
        gate_list.append(U3(3, 3, 3).control(1))
        gate_list.append(X().control(1))
        gate_list.append(CX().control(1))
        gate_list.append(XPow(3).control(1))
        gate_list.append(Y().control(1))
        gate_list.append(CY().control(1))
        gate_list.append(YPow().control(1))
        gate_list.append(CZ().control(1))
        gate_list.append(Z().control(1))
        gate_list.append(ZPow().control(1))
        # print(gate_list)
        for gate in gate_list:
            # print(gate,gate.__class__)
            # print(issubclass(ControlledGate,gate.__class__))
            # pip install pytest-check and pytest-assume if it doesn't work.
            pytest.assume(issubclass(ControlledGate, gate.__class__))

    def test_assemble_circuit(self):
        "Test assembling circuit."
        circ = Circuit(5)
        h = H()
        cnot = CX()
        print(type(H()))
        circ.append([h(i) for i in range(5)])
        circ.append([cnot([i, i + 1]) for i in range(4)])

        assert len(circ.moments) == 5

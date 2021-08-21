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
        """Tests two qubit gate."""
        ch = circuits.CH(global_phase=10)
        assert ch.num_qubits == 2

    def test_u3(self):
        """Tests U3 gate params."""
        u3 = circuits.U3(theta=0.3, phi=3, lam=10.0)
        assert u3.params == [0.3, 3, 10.0]

    @pytest.mark.skip(reason="pytest_assume.plugin.FailedAssumption")
    def test_create_control_gates(self):
        """Tests creating control gates."""
        gate_list = [
            H(2).control(1),
            DCX().control(1),
            CH().control(1),
            HPow(exponent=1.5).control(1),
            I().control(1),
            iSwap().control(1),
            Phase(1.1).control(1),
            CPhase(3.2).control(1),
            pSwap().control(1),
            R(1, 2).control(1),
            RX(2).control(1),
            RXX(3).control(1),
            RXY(1.2).control(1),
            RY(3).control(1),
            RYY(1.2).control(1),
            RZ(1.45).control(1),
            RZZ(3.1).control(1),
            RZX(1.2).control(1),
            S().control(1),
            Sdg().control(1),
            Swap().control(1),
            SX().control(1),
            SXdg().control(1),
            T().control(1),
            Tdg().control(1),
            U(1, 2, 3).control(1),
            U1(1).control(3),
            U2(1, 1.1).control(1),
            U3(3, 3, 3).control(1),
            X().control(1),
            CX().control(1),
            XPow(3).control(1),
            Y().control(1),
            CY().control(1),
            YPow().control(1),
            CZ().control(1),
            Z().control(1),
            ZPow().control(1),
        ]
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

        assert len(circ.moments) == 3

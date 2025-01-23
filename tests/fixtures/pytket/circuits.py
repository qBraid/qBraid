# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing pytket programs used for testing

"""
from pytket.circuit import Circuit as TKCircuit


def pytket_bell() -> TKCircuit:
    """Returns pytket bell circuit"""
    circuit = TKCircuit(2)
    circuit.H(0)
    circuit.CX(0, 1)
    return circuit


def pytket_shared15():
    """Returns pytket `Circuit` for qBraid `TestSharedGates`."""

    circuit = TKCircuit(4)

    for i in range(4):
        circuit.H(i)
    for i in range(2):
        circuit.X(i)
    circuit.Y(2)
    circuit.Z(3)
    circuit.S(0)
    circuit.Sdg(1)
    circuit.T(2)
    circuit.Tdg(3)
    circuit.Rx(1 / 4, 0)
    circuit.Ry(1 / 2, 1)
    circuit.Rz(3 / 4, 2)
    circuit.U1(1 / 8, 3)
    circuit.SX(0)
    circuit.SXdg(1)
    circuit.ISWAPMax(2, 3)
    for i in range(2):
        circuit.SWAP(i, i + 2)
    circuit.CX(0, 1)
    circuit.CU1(1 / 4, 2, 3)

    return circuit

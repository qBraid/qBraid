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
Module containing Pennylane Tapes used for testing

"""
import numpy as np
import pennylane as qml
from pennylane.tape import QuantumTape


def pennylane_bell() -> QuantumTape:
    """Returns Pennylane tape representing bell circuit"""
    with QuantumTape() as tape:
        qml.Hadamard(wires=0)
        qml.CNOT(wires=[0, 1])

    return tape


def pennylane_shared15() -> QuantumTape:
    """Returns Pennylane tape for shared gates tests."""
    with QuantumTape() as tape:
        qml.Hadamard(wires=0)
        qml.Hadamard(wires=1)
        qml.Hadamard(wires=2)
        qml.Hadamard(wires=3)
        qml.PauliX(wires=0)
        qml.PauliX(wires=1)
        qml.PauliY(wires=2)
        qml.PauliZ(wires=3)
        qml.S(wires=0)
        qml.adjoint(qml.S(wires=1))
        qml.T(wires=2)
        qml.adjoint(qml.T(wires=3))
        qml.RX(np.pi / 4, wires=0)
        qml.RY(np.pi / 2, wires=1)
        qml.RZ(3 * np.pi / 4, wires=2)
        qml.PhaseShift(np.pi / 8, wires=3)
        qml.SX(wires=0)
        qml.adjoint(qml.SX(wires=1))
        qml.ISWAP(wires=[2, 3])
        qml.SWAP(wires=[0, 2])
        qml.SWAP(wires=[1, 3])
        qml.CNOT(wires=[0, 1])
        qml.ControlledPhaseShift(np.pi / 4, wires=[2, 3])
    return tape

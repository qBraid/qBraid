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
Module containing Qiskit quantum circuits used for testing

"""
import numpy as np
from qiskit import QuantumCircuit


def qiskit_bell() -> QuantumCircuit:
    """Returns Qiskit bell circuit"""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    return circuit


def qiskit_shared15():
    """Returns qiskit `QuantumCircuit` for qBraid `TestSharedGates`."""

    circuit = QuantumCircuit(4)

    circuit.h([0, 1, 2, 3])
    circuit.x([0, 1])
    circuit.y(2)
    circuit.z(3)
    circuit.s(0)
    circuit.sdg(1)
    circuit.t(2)
    circuit.tdg(3)
    circuit.rx(np.pi / 4, 0)
    circuit.ry(np.pi / 2, 1)
    circuit.rz(3 * np.pi / 4, 2)
    circuit.p(np.pi / 8, 3)
    circuit.sx(0)
    circuit.sxdg(1)
    circuit.iswap(2, 3)
    circuit.swap([0, 1], [2, 3])
    circuit.cx(0, 1)
    circuit.cp(np.pi / 4, 2, 3)

    return circuit

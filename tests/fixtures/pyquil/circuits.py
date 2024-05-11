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
Module containing pyQuil programs used for testing

"""
import numpy as np
from pyquil import Program
from pyquil.gates import CNOT, CPHASE, ISWAP, RX, RY, RZ, SWAP, H, X, Y, Z


def pyquil_bell() -> Program:
    """Returns pyQuil bell circuit"""
    program = Program()
    program += H(0)
    program += CNOT(0, 1)
    return program


def pyquil_shared15() -> Program:
    """Returns pyquil `Program` for qBraid `TestSharedGates`."""

    p = Program()

    p += H(0)
    p += H(1)
    p += H(2)
    p += H(3)
    p += X(0)
    p += X(1)
    p += Y(2)
    p += Z(3)
    p += RZ(np.pi / 2, 0)  # S
    p += RZ(-np.pi / 2, 1)  # Sdg
    p += RZ(np.pi / 4, 2)  # T
    p += RZ(-np.pi / 4, 3)  # Tdg
    p += RX(np.pi / 4, 0)
    p += RY(np.pi / 2, 1)
    p += RZ(3 * np.pi / 4, 2)
    p += RZ(np.pi / 8, 3)
    p += RX(np.pi / 2, 0)
    p += RX(-np.pi / 2, 1)
    p += ISWAP(2, 3)
    p += SWAP(0, 2)
    p += SWAP(1, 3)
    p += CNOT(0, 1)
    p += CPHASE(np.pi / 4, 2, 3)

    return p

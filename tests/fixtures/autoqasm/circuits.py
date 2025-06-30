# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing AutoQASM programs used for testing
"""
import autoqasm as aq
import numpy as np
from autoqasm.instructions import (
    cnot,
    cphaseshift,
    h,
    iswap,
    phaseshift,
    rx,
    ry,
    rz,
    s,
    si,
    swap,
    t,
    ti,
    v,
    vi,
    x,
    y,
    z,
)

AutoQASMType = aq.program.program.Program


@aq.main
def autoqasm_bell_circuit():
    h(0)
    cnot(0, 1)


def autoqasm_bell() -> AutoQASMType:
    """Returns AutoQASM bell circuit."""
    return autoqasm_bell_circuit.build()


@aq.main
def autoqasm_shared15_circuit():
    for i in range(4):
        h(i)
    x(0)
    x(1)
    y(2)
    z(3)
    s(0)
    si(1)
    t(2)
    ti(3)
    rx(0, np.pi / 4)
    ry(1, np.pi / 2)
    rz(2, 3 * np.pi / 4)
    phaseshift(3, np.pi / 8)
    v(0)
    vi(1)
    iswap(2, 3)
    swap(0, 2)
    swap(1, 3)
    cnot(0, 1)
    cphaseshift(2, 3, np.pi / 4)


def autoqasm_shared15() -> AutoQASMType:
    """Returns AutoQASM `Circuit` for qBraid `TestSharedGates`."""
    return autoqasm_shared15_circuit.build()

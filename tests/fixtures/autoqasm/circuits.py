# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

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
Module containing Braket circuits used for testing

"""
import numpy as np
from braket.circuits import Circuit as BKCircuit


def braket_bell() -> BKCircuit:
    """Returns Braket bell circuit"""
    circuit = BKCircuit().h(0).cnot(0, 1)
    return circuit


def braket_shared15():
    """Returns braket `Circuit` for qBraid `TestSharedGates`."""

    circuit = BKCircuit()

    circuit.h([0, 1, 2, 3])
    circuit.x([0, 1])
    circuit.y(2)
    circuit.z(3)
    circuit.s(0)
    circuit.si(1)
    circuit.t(2)
    circuit.ti(3)
    circuit.rx(0, np.pi / 4)
    circuit.ry(1, np.pi / 2)
    circuit.rz(2, 3 * np.pi / 4)
    circuit.phaseshift(3, np.pi / 8)
    circuit.v(0)
    circuit.vi(1)
    circuit.iswap(2, 3)
    circuit.swap(0, 2)
    circuit.swap(1, 3)
    circuit.cnot(0, 1)
    circuit.cphaseshift(2, 3, np.pi / 4)

    return circuit

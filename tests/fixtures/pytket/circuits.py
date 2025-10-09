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

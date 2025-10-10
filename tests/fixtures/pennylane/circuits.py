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

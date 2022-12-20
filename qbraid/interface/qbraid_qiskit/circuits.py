# Copyright 2023 qBraid
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
Module containing Qiskit quantum circuits used for testing

"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.exceptions import CircuitError
from qiskit.circuit.random import random_circuit

from qbraid.exceptions import QbraidError


def _qiskit_random(num_qubits: int, depth: int, **kwargs) -> QuantumCircuit:
    """Generate random circuit qiskit circuit.

    Args:
        num_qubits (int): number of quantum wires
        depth (int): layers of operations (i.e. critical path length)

    Raises:
        QbraidError: When invalid qiskit random circuit options given

    Returns:
        Qiskit random circuit

    """
    if "measure" not in kwargs:
        kwargs["measure"] = False

    try:
        return random_circuit(num_qubits, depth, **kwargs)
    except CircuitError as err:
        raise QbraidError("Could not create Qiskit random circuit") from err


def qiskit_bell() -> QuantumCircuit:
    """Returns Qiskit bell circuit"""
    circuit = QuantumCircuit(2)
    circuit.h(1)
    circuit.cx(1, 0)
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

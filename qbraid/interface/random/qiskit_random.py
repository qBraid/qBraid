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
Module for generating random Qiskit circuits

"""
from qiskit import QuantumCircuit
from qiskit.circuit.exceptions import CircuitError
from qiskit.circuit.random import random_circuit

from qbraid.exceptions import QbraidError


def qiskit_random(num_qubits: int, depth: int, **kwargs) -> QuantumCircuit:
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
    except (CircuitError, ValueError, TypeError) as err:
        raise QbraidError("Failed to create Qiskit random circuit") from err

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
Module for generating random Qiskit circuits

"""
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
    except (CircuitError, ValueError) as err:
        raise QbraidError("Failed to create Qiskit random circuit") from err

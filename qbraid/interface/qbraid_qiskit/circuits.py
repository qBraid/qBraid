"""Qiskit quantum circuits used for testing"""

import numpy as np
from typing import Optional
from qiskit import QuantumCircuit
from qiskit.circuit.exceptions import CircuitError
from qiskit.circuit.random import random_circuit

from qbraid.exceptions import QbraidError


def qiskit_bell():
    circuit = QuantumCircuit(2)
    circuit.h(1)
    circuit.cx(1, 0)
    return circuit


def qiskit_random_circuit(
    num_qubits: Optional[int], depth: Optional[int], measure: Optional[bool] = False
) -> QuantumCircuit:
    """Generate random circuit of arbitrary size and form. If not provided, num_qubits
    and depth are randomly selected in range [2, 4].

    Args:
        num_qubits (int): number of quantum wires
        depth (int): layers of operations (i.e. critical path length)
        measure (bool): if True, measure all qubits at the end

    Returns:
        Qiskit circuit

    Raises:
        QbraidError: when invalid options given

    """
    num_qubits = num_qubits if num_qubits else np.random.randint(1, 4)
    depth = depth if depth else np.random.randint(1, 4)
    try:
        return random_circuit(num_qubits, depth, measure=measure)
    except CircuitError as err:
        raise QbraidError from err

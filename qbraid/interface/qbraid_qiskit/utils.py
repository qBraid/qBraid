"""Functions to convert between Cirq's circuit representation and
Qiskit's circuit representation.
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

QASMType = str


def _unitary_from_qiskit(circuit: QuantumCircuit) -> np.ndarray:
    """Calculate unitary of a qiskit circuit. Note: Qiskit circuits are always constructed
    with contiguous qubit indexing."""
    return Operator(circuit).data

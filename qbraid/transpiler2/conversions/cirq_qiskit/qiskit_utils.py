"""Qiskit utility module"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

def unitary_from_qiskit(circuit: QuantumCircuit, ensure_contiguous=False) -> np.ndarray:
    """Calculate unitary of a qiskit circuit. Note: Qiskit circuits are always constructed
    with contiguous qubit indexing."""
    return Operator(circuit).data

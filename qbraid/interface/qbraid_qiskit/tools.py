"""Qiskit tools"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

QASMType = str


def _unitary_from_qiskit(circuit: QuantumCircuit) -> np.ndarray:
    """Return the unitary of a Qiskit quantum circuit."""
    return Operator(circuit).data

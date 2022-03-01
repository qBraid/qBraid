"""Braket unitary calculation module"""

import numpy as np
from cirq import Circuit
from braket.circuits.unitary_calculation import calculate_unitary

def _unitary_from_braket(circuit: Circuit) -> np.ndarray:
    """Calculate unitary of a braket circuit."""
    return calculate_unitary(circuit.qubit_count, circuit.instructions)
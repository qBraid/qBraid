"""Pennylane tools"""

import numpy as np
import pennylane as qml
from pennylane.tape import QuantumTape


def _unitary_from_pennylane(tape: QuantumTape) -> np.ndarray:
    """Return the unitary of a Pennylane quantum tape."""
    return qml.matrix(tape)

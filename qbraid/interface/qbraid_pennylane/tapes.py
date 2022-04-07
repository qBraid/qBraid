"""Pennylane quantum tapes used for testing"""

import pennylane as qml
from pennylane.tape import QuantumTape


def pennylane_bell():
    with QuantumTape() as tape:
        qml.Hadamard(wires=0)
        qml.CNOT(wires=[0, 1])
    return tape

"""Braket circuits used for testing"""

from braket.circuits import Circuit as BKCircuit


def braket_bell():
    circuit = BKCircuit().h(1).cnot(1, 0)
    return circuit

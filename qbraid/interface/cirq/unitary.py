from cirq import Circuit

def unitary_from_cirq(circuit: Circuit):
    """Calculate unitary of a cirq circuit."""
    return circuit.unitary()
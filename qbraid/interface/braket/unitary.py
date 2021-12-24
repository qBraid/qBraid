from braket.circuits import Circuit
from braket.circuits.unitary_calculation import calculate_unitary

from .contiguous import make_contiguous

def unitary_from_braket(circuit: Circuit):
    """Calculate unitary of a braket circuit."""
    contiguous_circuit = make_contiguous(circuit)
    return calculate_unitary(contiguous_circuit.qubit_count, contiguous_circuit.instructions)
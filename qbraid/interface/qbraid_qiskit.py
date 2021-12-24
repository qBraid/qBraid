from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator as QiskitOperator

def unitary_from_qiskit(circuit: QuantumCircuit):
    """Calculate unitary of a qiskit circuit."""
    return QiskitOperator(circuit).data
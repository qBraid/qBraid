from qbraid.interface import random_circuit
from qbraid import circuit_wrapper
from qiskit import QuantumCircuit
import numpy as np

if __name__ == "__main__":
    
    circuit = random_circuit("qiskit", measure=True)
    qbraid_circuit = circuit_wrapper(circuit)
    braket_circuit = qbraid_circuit.transpile("braket")
    print(circuit)
    print(braket_circuit)
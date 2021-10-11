"""Utility functions for generating random circuits."""

from numpy.random import randint
from qiskit.circuit.exceptions import CircuitError as QiskitCircuitError
from qiskit.circuit.random import random_circuit as qiskit_random_circuit

import qbraid
from qbraid.circuits.exceptions import CircuitError


def random_circuit(package, num_qubits=None, depth=None, measure=False):
    """Generate random circuit of arbitrary size and form. If not provided, num_qubits
    and depth are randomly selected in range [2, 4].

    Args:
        package (str): qbraid supported software package
        num_qubits (int): number of quantum wires
        depth (int): layers of operations (i.e. critical path length)
        measure (bool): if True, measure all qubits at the end

    Returns:
        CircuitWrapper: qbraid circuit wrapper object

    Raises:
        CircuitError: when invalid options given

    """
    num_qubits = num_qubits if num_qubits else randint(1, 4)
    depth = depth if depth else randint(1, 4)
    try:
        qiskit_circuit = qiskit_random_circuit(num_qubits, depth, measure=measure)
    except QiskitCircuitError as err:
        raise CircuitError(str(err)) from err
    if package == "qiskit":
        return qiskit_circuit
    qbraid_circuit = qbraid.circuit_wrapper(qiskit_circuit)
    package_circuit = qbraid_circuit.transpile(package)
    return package_circuit

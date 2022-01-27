"""Utility functions for generating random circuits."""

from cirq.testing import random_circuit as cirq_random_circuit
from numpy.random import randint
from qiskit.circuit.exceptions import CircuitError as QiskitCircuitError
from qiskit.circuit.random import random_circuit as qiskit_random_circuit

import qbraid


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
        ValueError: when invalid options given

    """
    num_qubits = num_qubits if num_qubits else randint(1, 4)
    depth = depth if depth else randint(1, 4)
    seed = randint(1, 11)
    if package == "cirq":
        try:
            return cirq_random_circuit(num_qubits, n_moments=depth, op_density=1, random_state=seed)
        except ValueError as err:
            raise ValueError from err
    try:
        random_circuit = qiskit_random_circuit(num_qubits, depth, measure=measure)
    except QiskitCircuitError as err:
        raise ValueError from err
    if package == "qiskit":
        return random_circuit
    elif package == "braket":
        qbraid_circuit = qbraid.circuit_wrapper(random_circuit)
        return qbraid_circuit.transpile(package)
    else:
        raise ValueError(
            f"{package} is not a supported package. \n"
            "Supported packages include qiskit, cirq, braket. "
        )

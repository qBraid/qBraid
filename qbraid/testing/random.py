"""Module for generating random circuits"""

from typing import Optional

from qbraid import QPROGRAM, circuit_wrapper
from qbraid.exceptions import QbraidError


def random_circuit(
    package: str, 
    num_qubits: Optional[int], 
    depth: Optional[int], 
    measure: Optional[bool]=False
) -> QPROGRAM:
    """Generate random circuit of arbitrary size and form. If not provided, num_qubits
    and depth are randomly selected in range [2, 4].

    Args:
        package (str): qbraid supported software package
        num_qubits (int): number of quantum wires
        depth (int): layers of operations (i.e. critical path length)
        measure (bool): if True, measure all qubits at the end

    Returns:
        QPROGRAM: qbraid supported quantum circuit/program

    Raises:
        QbraidError: when invalid options given

    """
    from cirq.testing import random_circuit as cirq_random_circuit
    from numpy import random
    from qiskit.circuit.exceptions import CircuitError as QiskitCircuitError
    from qiskit.circuit.random import random_circuit as qiskit_random_circuit

    num_qubits = num_qubits if num_qubits else random.randint(1, 4)
    depth = depth if depth else random.randint(1, 4)
    seed = random.randint(1, 11)
    if package == "qiskit":
        try:
            return qiskit_random_circuit(num_qubits, depth, measure=measure)
        except QiskitCircuitError as err:
            raise QbraidError from err
    try:
        random_circuit = cirq_random_circuit(
            num_qubits, n_moments=depth, op_density=1, random_state=seed
        )
    except ValueError as err:
        raise QbraidError from err
    if package == "cirq":
        return random_circuit
    elif package == "braket":
        return circuit_wrapper(random_circuit).transpile("braket")
    else:
        raise QbraidError(
            f"{package} is not a supported package. \n"
            "Supported packages include qiskit, cirq, braket. "
        )
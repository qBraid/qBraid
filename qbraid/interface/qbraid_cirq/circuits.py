"""Cirq circuits used for testing"""

from typing import Optional

import numpy as np
from cirq import Circuit, LineQubit, ops
from cirq.testing import random_circuit

from qbraid.exceptions import QbraidError


def cirq_bell():
    q0, q1 = LineQubit.range(2)
    circuit = Circuit(ops.H(q0), ops.CNOT(q0, q1))
    return circuit


def cirq_random_circuit(
    num_qubits: Optional[int], depth: Optional[int], measure: Optional[bool] = False
) -> Circuit:
    """Generate random circuit of arbitrary size and form. If not provided, num_qubits
    and depth are randomly selected in range [2, 4].

    Args:
        num_qubits (int): number of quantum wires
        depth (int): layers of operations (i.e. critical path length)
        measure (bool): if True, measure all qubits at the end

    Returns:
        A Cirq circuit

    Raises:
        QbraidError: when invalid options given

    """
    num_qubits = num_qubits if num_qubits else np.random.randint(1, 4)
    depth = depth if depth else np.random.randint(1, 4)
    seed = np.random.randint(1, 11)
    try:
        return random_circuit(num_qubits, n_moments=depth, op_density=1, random_state=seed)
    except ValueError as err:
        raise QbraidError from err

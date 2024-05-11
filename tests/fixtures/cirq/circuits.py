# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing Cirq circuits used for testing

"""
import random
from typing import Optional

import numpy as np
from cirq import (
    CNOT,
    ISWAP,
    SWAP,
    Circuit,
    CZPowGate,
    H,
    LineQubit,
    S,
    T,
    X,
    XPowGate,
    Y,
    Z,
    ZPowGate,
    measure,
    ops,
    rx,
    ry,
    rz,
)


def cirq_bell() -> Circuit:
    """Returns Cirq bell circuit"""
    q0, q1 = LineQubit.range(2)
    circuit = Circuit(ops.H(q0), ops.CNOT(q0, q1))
    return circuit


def cirq_shared15():
    """Returns cirq `Circuit` for qBraid `TestSharedGates`."""

    circuit = Circuit()
    q0, q1, q2, q3 = LineQubit.range(4)

    cirq_shared_gates = [
        H(q0),
        H(q1),
        H(q2),
        H(q3),
        X(q0),
        X(q1),
        Y(q2),
        Z(q3),
        S(q0),
        ZPowGate(exponent=-0.5)(q1),
        T(q2),
        ZPowGate(exponent=-0.25)(q3),
        rx(rads=np.pi / 4)(q0),
        ry(rads=np.pi / 2)(q1),
        rz(rads=3 * np.pi / 4)(q2),
        ZPowGate(exponent=1 / 8)(q3),
        XPowGate(exponent=0.5)(q0),
        XPowGate(exponent=-0.5)(q1),
        ISWAP(q2, q3),
        SWAP(q0, q2),
        SWAP(q1, q3),
        CNOT(q0, q1),
        CZPowGate(exponent=0.25)(q2, q3),
    ]

    for gate in cirq_shared_gates:
        circuit.append(gate)

    return circuit


def sparse_circuit(num_qubits: Optional[int] = None) -> Circuit:
    """
    Generates a quantum circuit designed to benchmark the performance of a sparse simulator.

    This circuit is structured to maintain a level of sparsity in the system's state vector, making
    it a good candidate for testing sparse quantum simulators. Sparse simulators excel in
    simulating circuits where the state vector remains sparse, i.e., most of its elements are zero
    or can be efficiently represented.

    Args:
        num_qubits (optional, int): The number of qubits to use in the circuit. If not provided,
                                    a random number of qubits between 10 and 20 will be used.

    Returns:
        cirq.Circuit: The constructed circuit for benchmarking
    """
    num_qubits = num_qubits or random.randint(10, 20)
    # Create a circuit
    circuit = Circuit()

    # Create qubits
    qubits = LineQubit.range(num_qubits)

    # Apply Hadamard gates to the first half of the qubits
    for qubit in qubits[: num_qubits // 2]:
        circuit.append(H(qubit))

    # Apply a CNOT ladder
    for i in range(num_qubits - 1):
        circuit.append(CNOT(qubits[i], qubits[i + 1]))

    # Apply Z gates to randomly selected qubits
    for qubit in random.sample(qubits, k=num_qubits // 2):
        circuit.append(Z(qubit))

    # Measurement (optional)
    circuit.append(measure(*qubits, key="result"))

    return circuit

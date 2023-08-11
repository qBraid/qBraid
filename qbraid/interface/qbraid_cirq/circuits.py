# Copyright (C) 2023 qBraid
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
    ops,
    rx,
    ry,
    rz,
)
from cirq.testing import random_circuit

from qbraid.exceptions import QbraidError


def _cirq_random(num_qubits: int, depth: int, **kwargs) -> Circuit:
    """Generate random circuit of arbitrary size and form.

    Args:
        num_qubits (int): number of quantum wires
        depth (int): layers of operations (i.e. critical path length)

    Raises:
        QbraidError: When invalid cirq random circuit options given

    Returns:
        Cirq random circuit

    """
    if "random_state" not in kwargs:
        kwargs["random_state"] = np.random.randint(1, 11)

    if "op_density" not in kwargs:
        kwargs["op_density"] = 1

    try:
        return random_circuit(num_qubits, n_moments=depth, **kwargs)
    except ValueError as err:
        raise QbraidError("Could not create Cirq random circuit") from err


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

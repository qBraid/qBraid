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
Module for generating random Cirq circuits

"""
import jax
from cirq import Circuit
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
        key = jax.random.PRNGKey(0)
        key, subkey = jax.random.split(key)
        random_seed = int(jax.random.randint(subkey, (1,), 1, 11)[0])
        kwargs["random_state"] = random_seed

    if "op_density" not in kwargs:
        kwargs["op_density"] = 1

    try:
        return random_circuit(num_qubits, n_moments=depth, **kwargs)
    except ValueError as err:
        raise QbraidError("Could not create Cirq random circuit") from err

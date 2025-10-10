# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module for generating random Cirq circuits

"""
import numpy as np
from cirq import Circuit
from cirq.testing import random_circuit

from qbraid.exceptions import QbraidError


def cirq_random(num_qubits: int, depth: int, **kwargs) -> Circuit:
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
    except (ValueError, TypeError) as err:
        raise QbraidError("Failed to create Cirq random circuit") from err

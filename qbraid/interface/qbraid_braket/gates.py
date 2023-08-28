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
Module for generating dictionary of all braket gates for testing/benchmarking

"""

import string
from typing import List, Optional

import numpy as np
import scipy
from braket.circuits import Gate


def generate_params(varnames: List[str], seed: Optional[int] = None):
    """Returns a dictionary of random parameters for a given list of variable names"""
    if seed is not None:
        np.random.seed(seed)
    params = {}
    for v in varnames:
        if v.startswith("angle"):
            params[v] = np.random.rand() * 2 * np.pi
    return params


def get_braket_gates(seed: Optional[int] = None):
    """Returns a dictionary of all braket gates with random parameters"""
    braket_gates = {attr: None for attr in dir(Gate) if attr[0] in string.ascii_uppercase}
    for gate in ["C", "PulseGate"]:
        braket_gates.pop(gate, None)

    for gate in braket_gates:
        if gate == "Unitary":
            n = np.random.randint(1, 4)
            unitary = scipy.stats.unitary_group.rvs(2**n)
            braket_gates[gate] = getattr(Gate, gate)(matrix=unitary)
        else:
            varnames = [v for v in getattr(Gate, gate).__init__.__code__.co_varnames if v != "self"]
            params = generate_params(varnames, seed=seed)
            braket_gates[gate] = getattr(Gate, gate)(**params)

    return {k: v for k, v in braket_gates.items() if v is not None}

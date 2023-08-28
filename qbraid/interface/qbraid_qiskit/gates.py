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
Module for generating dictionary of all qiskit gates for testing/benchmarking

"""

import string
from typing import List, Optional

import numpy as np
from qiskit.circuit.library import standard_gates


def generate_params(varnames: List[str], seed: Optional[int] = None):
    """Returns a dictionary of random parameters for a given list of variable names"""
    if seed is not None:
        np.random.seed(seed)
    params = {
        ra: np.random.rand() * 2 * np.pi
        for ra in ["theta", "phi", "lam", "gamma"]
        if ra in varnames
    }
    if "num_ctrl_qubits" in varnames:
        params["num_ctrl_qubits"] = np.random.randint(1, 7)
    if "phase" in varnames:
        params["phase"] = np.random.rand() * 2 * np.pi
    return params


def get_qiskit_gates(seed: Optional[int] = None):
    """Returns a dictionary of all qiskit gates with random parameters"""
    qiskit_gates = {attr: None for attr in dir(standard_gates) if attr[0] in string.ascii_uppercase}
    for gate in qiskit_gates:
        varnames = [
            v for v in getattr(standard_gates, gate).__init__.__code__.co_varnames if v != "self"
        ]
        params = generate_params(varnames, seed=seed)
        qiskit_gates[gate] = getattr(standard_gates, gate)(**params)
    return {k: v for k, v in qiskit_gates.items() if v is not None}

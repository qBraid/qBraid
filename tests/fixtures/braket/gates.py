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
Module for generating dictionary of all braket gates for testing/benchmarking

"""

import string
from typing import Optional

import numpy as np
import scipy
from braket.circuits import Gate
from braket.circuits.gates import (
    CY,
    CZ,
    XX,
    XY,
    YY,
    ZZ,
    CCNot,
    CNot,
    CPhaseShift,
    H,
    I,
    ISwap,
    PhaseShift,
    PSwap,
    Rx,
    Ry,
    Rz,
    S,
    Si,
    Swap,
    T,
    Ti,
    V,
    Vi,
    X,
    Y,
    Z,
)

braket_gates = {
    # one-qubit, zero parameter
    "H": H,
    "X": X,
    "Y": Y,
    "Z": Z,
    "S": S,
    "Sdg": Si,
    "T": T,
    "Tdg": Ti,
    "I": I,
    "SX": V,
    "SXdg": Vi,
    # one-qubit, one parameter
    "Phase": PhaseShift,
    "RX": Rx,
    "RY": Ry,
    "RZ": Rz,
    "U1": PhaseShift,
    # two-qubit, zero parameter
    # 'CH':BraketGate.,
    "CX": CNot,
    "Swap": Swap,
    "iSwap": ISwap,
    # 'CSX':BraketGate.,
    # 'DCX': BraketGate.,
    "CY": CY,
    "CZ": CZ,
    # two-qubit, one parameter
    "RXX": XX,
    "RXY": XY,
    "RYY": YY,
    "RZZ": ZZ,
    "pSwap": PSwap,
    "CPhase": CPhaseShift,
    # multi-qubit
    "CCX": CCNot,
    # unitary
    # "Unitary": Unitary,
}


def generate_params(varnames: list[str], seed: Optional[int] = None):
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
    for gate in ["C", "PulseGate", "GPhase"]:
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

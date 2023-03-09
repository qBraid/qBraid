# Copyright 2023 qBraid
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
Module for Braket gate dictionary used for testing

"""
from braket.circuits.gates import (  # Unitary,
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

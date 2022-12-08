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
Module defining input / output types for a quantum backend:

  * QUANTUM_PROGRAM: Type alias defining all supported quantum circuit / program types

  * SUPPORTED_FRONTENDS: List of all supported quantum software packages

"""
from typing import Union

from braket.circuits import Circuit as _BraketCircuit
from cirq import Circuit as _CirqCircuit
from pennylane.tape import QuantumTape as _PennylaneTape
from pyquil import Program as _pyQuilProgram
from qiskit import QuantumCircuit as _QiskitCircuit

# Supported quantum programs.
QUANTUM_PROGRAM = Union[
    _BraketCircuit, _CirqCircuit, _PennylaneTape, _QiskitCircuit, _pyQuilProgram
]

_PROGRAMS = [_BraketCircuit, _CirqCircuit, _PennylaneTape, _QiskitCircuit, _pyQuilProgram]

# pylint: disable-next=bad-str-strip-call
SUPPORTED_PROGRAMS = [str(x).strip("<class").strip(">").strip(" ").strip("'") for x in _PROGRAMS]

SUPPORTED_FRONTENDS = [x.split(".")[0] for x in SUPPORTED_PROGRAMS]

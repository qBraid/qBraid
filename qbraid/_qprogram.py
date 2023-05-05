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
Module defining input / output types for a quantum backend:

  * QPROGRAM: Type alias defining all supported quantum circuit / program types

  * QPROGRAM_LIBS: List of all supported quantum software libraries / packages

"""
from typing import Union

from braket.circuits import Circuit as _BraketCircuit
from cirq import Circuit as _CirqCircuit
from pyquil import Program as _pyQuilProgram
from pytket.circuit import Circuit as _PytketCircuit
from qiskit import QuantumCircuit as _QiskitCircuit

# Supported quantum programs.
QPROGRAM = Union[_BraketCircuit, _CirqCircuit, _QiskitCircuit, _pyQuilProgram, _PytketCircuit]

_PROGRAMS = [_BraketCircuit, _CirqCircuit, _QiskitCircuit, _pyQuilProgram, _PytketCircuit]

# pylint: disable-next=bad-str-strip-call
QPROGRAM_TYPES = [str(x).strip("<class").strip(">").strip(" ").strip("'") for x in _PROGRAMS]

QPROGRAM_LIBS = [x.split(".")[0] for x in QPROGRAM_TYPES]

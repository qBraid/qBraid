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

import braket.circuits
import cirq
import pyquil
import pytket.circuit
import qiskit

# Supported quantum programs.
QASMType = str

QPROGRAM = Union[
    braket.circuits.Circuit,
    cirq.Circuit,
    qiskit.QuantumCircuit,
    pyquil.Program,
    pytket.circuit.Circuit,
    QASMType,
]

_PROGRAMS = [
    braket.circuits.Circuit,
    cirq.Circuit,
    qiskit.QuantumCircuit,
    pyquil.Program,
    pytket.circuit.Circuit,
]


# pylint: disable-next=bad-str-strip-call
_PROGRAM_TYPES = [str(x).strip("<class").strip(">").strip(" ").strip("'") for x in _PROGRAMS]
QPROGRAM_TYPES = _PROGRAMS + [QASMType]

_PROGRAM_LIBS = [x.split(".")[0] for x in _PROGRAM_TYPES]
QPROGRAM_LIBS = _PROGRAM_LIBS + ["qasm2", "qasm3"]

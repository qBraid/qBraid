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

"""Defines input types for a quantum backend"""
from typing import Union

from cirq import Circuit as _CirqCircuit
from qiskit import QuantumCircuit as _QiskitCircuit
from braket.circuits import Circuit as _BraketCircuit

# Supported quantum programs.
SUPPORTED_PROGRAM_TYPES = {
    "cirq": "Circuit",
    "qiskit": "QuantumCircuit",
    "braket": "Circuit",
}

# Supported + installed quantum programs.
QPROGRAM = Union[_CirqCircuit, _QiskitCircuit, _BraketCircuit]
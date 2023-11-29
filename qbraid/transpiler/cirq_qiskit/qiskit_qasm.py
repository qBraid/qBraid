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
Module defining Qiskit OpenQASM conversions

"""

from qiskit import QuantumCircuit
from qiskit.qasm3 import dumps, loads


def qiskit_from_qasm2(qasm_str: str) -> QuantumCircuit:
    """Convert QASM 2.0 string to qiskit QuantumCircuit repr"""
    return QuantumCircuit.from_qasm_str(qasm_str)


def qiskit_to_qasm2(circuit: QuantumCircuit) -> str:
    """Convert qiskit QuantumCircuit to QASM 2.0 string"""
    return circuit.qasm()


def qiskit_from_qasm3(qasm_str: str) -> QuantumCircuit:
    """Convert QASM 3.0 string to qiskit QuantumCircuit repr"""
    return loads(qasm_str)


def qiskit_to_qasm3(circuit: QuantumCircuit) -> str:
    """Convert qiskit QuantumCircuit to QASM 3.0 string"""
    return dumps(circuit)

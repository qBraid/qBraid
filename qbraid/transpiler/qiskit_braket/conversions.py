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
Module containing functions to convert between Qiskit's circuit
representation and Braket's circuit representation via OpenQASM 3.0.

"""
import braket.circuits
import qiskit

from qbraid.transpiler.cirq_braket.braket_qasm import braket_from_qasm3, braket_to_qasm3
from qbraid.transpiler.cirq_qiskit.qiskit_qasm import qiskit_from_qasm3, qiskit_to_qasm3


def braket_to_qiskit(circuit: braket.circuits.Circuit) -> qiskit.QuantumCircuit:
    """Convert an Amazon Braket circuit to a Qiskit circuit via OpenQASM 3.

    Args:
        circuit (braket.circuits.Circuit): Braket circuit to convert.
    Returns:
        qiskit.QuantumCircuit: Qiskit circuit.
    """
    qasm3_str = braket_to_qasm3(circuit)
    return qiskit_from_qasm3(qasm3_str)


def qiskit_to_braket(circuit: qiskit.QuantumCircuit) -> braket.circuits.Circuit:
    """Convert a Qiskit circuit to an Amazon Braket circuit via OpenQASM 3.

    Args:
        circuit (qiskit.QuantumCircuit): Qiskit circuit to convert.
    Returns:
        braket.circuits.Circuit: Braket circuit.
    """
    qasm3_str = qiskit_to_qasm3(circuit)
    return braket_from_qasm3(qasm3_str)

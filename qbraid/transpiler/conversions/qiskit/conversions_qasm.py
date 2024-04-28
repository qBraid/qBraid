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
import qiskit
from qiskit.qasm2 import dumps as qasm2_dumps
from qiskit.qasm3 import QASM3ImporterError, dumps, loads

from qbraid.transforms.qasm3.compat import qasm3_braket_post_process


def qasm3_to_qiskit(qasm3: str) -> qiskit.QuantumCircuit:
    """Convert QASM 3.0 string to a Qiskit QuantumCircuit representation.

    Args:
        qasm3 (str): A string in QASM 3.0 format.

    Returns:
        qiskit.QuantumCircuit: A QuantumCircuit object representing the input QASM 3.0 string.
    """
    try:
        return loads(qasm3)
    except QASM3ImporterError:
        pass

    qasm3 = qasm3_braket_post_process(qasm3)

    return loads(qasm3)


def qiskit_to_qasm3(circuit: qiskit.QuantumCircuit) -> str:
    """Convert qiskit QuantumCircuit to QASM 3.0 string"""
    return dumps(circuit)


def qasm2_to_qiskit(qasm: str) -> qiskit.QuantumCircuit:
    """Returns a Qiskit circuit equivalent to the input OpenQASM 2 string.

    Args:
        qasm: OpenQASM 2 string to convert to a Qiskit circuit.

    Returns:
        Qiskit.QuantumCircuit object equivalent to the input OpenQASM 2 string.
    """
    return qiskit.QuantumCircuit.from_qasm_str(qasm)


def qiskit_to_qasm2(circuit: qiskit.QuantumCircuit) -> str:
    """Returns OpenQASM 2 string equivalent to the input Qiskit circuit.

    Args:
        circuit: Qiskit circuit to convert to OpenQASM 2 string.

    Returns:
        str: OpenQASM 2 representation of the input Qiskit circuit.
    """
    return qasm2_dumps(circuit)

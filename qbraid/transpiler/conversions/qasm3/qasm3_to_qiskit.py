# Copyright (C) 2024 qBraid
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
from qiskit.qasm3 import QASM3ImporterError, loads

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

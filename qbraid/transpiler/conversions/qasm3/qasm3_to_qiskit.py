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
from typing import TYPE_CHECKING

from qbraid._import import LazyLoader
from qbraid.transforms.qasm3.compat import transform_notation_from_external

qiskit_qasm3 = LazyLoader("qiskit_qasm3", globals(), "qiskit.qasm3")


if TYPE_CHECKING:
    import qiskit as qiskit_


def qasm3_to_qiskit(qasm3: str) -> "qiskit_.QuantumCircuit":
    """Convert QASM 3.0 string to a Qiskit QuantumCircuit representation.

    Args:
        qasm3 (str): A string in QASM 3.0 format.

    Returns:
        qiskit.QuantumCircuit: A QuantumCircuit object representing the input QASM 3.0 string.
    """
    try:
        return qiskit_qasm3.loads(qasm3)
    except qiskit_qasm3.QASM3ImporterError:
        pass

    qasm3 = transform_notation_from_external(qasm3)

    return qiskit_qasm3.loads(qasm3)

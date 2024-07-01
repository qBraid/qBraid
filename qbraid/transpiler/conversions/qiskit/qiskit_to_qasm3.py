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
from qiskit.qasm3 import dumps

from qbraid.transpiler.annotations import weight


@weight(1)
def qiskit_to_qasm3(circuit: qiskit.QuantumCircuit) -> str:
    """Convert qiskit QuantumCircuit to QASM 3.0 string"""
    return dumps(circuit)

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


def qasm2_to_qiskit(qasm: str) -> qiskit.QuantumCircuit:
    """Returns a Qiskit circuit equivalent to the input OpenQASM 2 string.

    Args:
        qasm: OpenQASM 2 string to convert to a Qiskit circuit.

    Returns:
        Qiskit.QuantumCircuit object equivalent to the input OpenQASM 2 string.
    """
    return qiskit.QuantumCircuit.from_qasm_str(qasm)

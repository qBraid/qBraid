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
Module for converting Pennylane QuantumTapes to and from OpenQASM

"""

import pennylane as qml
from pennylane.tape import QuantumTape
from pennylane.wires import Wires

from qbraid.interface.qbraid_qasm.tools import qasm_num_qubits


def to_qasm(tape: QuantumTape, **kwargs) -> str:
    """Convert Pennylane QuantumTape to OpenQASM 2.0 string.

    Args:
        tape: Pennylane tape to convert to qasm string

    Returns:
        OpenQASM 2.0 string equivalent to the input Pennylane QuantumTape."""
    return tape.to_openqasm(**kwargs)


def from_qasm(qasm_str: str) -> QuantumTape:
    """Convert OpenQASM 2.0 string to Pennylane QuantumTape.

    Args:
        qasm_str: OpenQASM 2.0 string to convert to Pennylane tape

    Returns:
        Pennylane QuantumTape equivalent to the input OpenQASM 2.0 string
    """
    num_wires = qasm_num_qubits(qasm_str)
    qml_template = qml.from_qasm(qasm_str)

    with QuantumTape() as tape:
        qml_template(wires=Wires(range(num_wires)))

    return tape

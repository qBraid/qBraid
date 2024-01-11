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
Module containing functions to convert between OpenQASM 2 and PyTKET.

"""
from typing import TYPE_CHECKING

from pytket.qasm import circuit_from_qasm_str, circuit_to_qasm_str

if TYPE_CHECKING:
    import pytket.circuit


def qasm2_to_pytket(qasm: str) -> "pytket.circuit.Circuit":
    """Returns a pytket circuit equivalent to the input OpenQASM 2 string.

    Args:
        qasm (str): OpenQASM 2 string to convert to a pytket circuit.

    Returns:
        pytket.circuit.Circuit: PyTKET circuit object equivalent to input OpenQASM 2 string.
    """
    return circuit_from_qasm_str(qasm)


def pytket_to_qasm2(circuit: "pytket.circuit.Circuit") -> str:
    """Returns an OpenQASM 2 string equivalent to the input pytket circuit.

    Args:
        circuit (pytket.circuit.Circuit): PyTKET circuit to convert to OpenQASM 2 string.

    Returns:
        str: OpenQASM 2 string equivalent to input pytket circuit.
    """
    return circuit_to_qasm_str(circuit)

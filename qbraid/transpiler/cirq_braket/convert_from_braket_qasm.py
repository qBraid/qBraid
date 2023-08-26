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
Module for converting Braket circuits to Cirq circuit via OpenQASM

"""

from braket.circuits import Circuit as BKCircuit
from cirq import Circuit
from cirq.contrib.qasm_import.exception import QasmException

from qbraid.interface import convert_to_contiguous
from qbraid.interface.qbraid_braket.qasm import braket_to_qasm
from qbraid.transpiler.cirq_qasm import from_qasm
from qbraid.transpiler.exceptions import CircuitConversionError


def from_braket(circuit: BKCircuit) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Braket circuit.

    Note: The returned Cirq circuit acts on cirq.LineQubit's with indices equal
    to the qubit indices of the Braket circuit.

    Args:
        circuit: Braket circuit to convert to a Cirq circuit.

    Raises:
        CircuitConversionError: if circuit could not be converted
    """
    compat_circuit = convert_to_contiguous(circuit)
    qasm_str = braket_to_qasm(compat_circuit)
    try:
        return from_qasm(qasm_str)
    except QasmException as err:
        raise CircuitConversionError("Error converting qasm string to Cirq circuit") from err

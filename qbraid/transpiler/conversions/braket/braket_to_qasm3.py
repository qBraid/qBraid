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
Module for converting Braket circuits to OpenQASM 3.0

"""
import pyqasm
from braket.circuits import Circuit
from braket.circuits.serialization import IRType

from qbraid.transpiler.annotations import weight


@weight(1)
def braket_to_qasm3(circuit: Circuit) -> str:
    """Converts a ``braket.circuits.Circuit`` to an OpenQASM 3.0 string.

    Args:
        circuit: Amazon Braket quantum circuit

    Returns:
        The OpenQASM 3.0 string equivalent to the circuit

    Raises:
        ProgramConversionError: If braket to qasm conversion fails

    """
    has_measurements = any(str(instr.operator) == "Measure" for instr in circuit.instructions)
    qasm_program = circuit.to_ir(IRType.OPENQASM).source
    qasm_module = pyqasm.load(qasm_program)
    qasm_module.unroll()
    if not has_measurements:
        qasm_module.remove_measurements()
    return qasm_module.unrolled_qasm

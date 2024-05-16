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
Module for converting Braket circuits to/from OpenQASM 3

"""
from typing import TYPE_CHECKING

from qbraid._import import LazyLoader
from qbraid.programs import QasmError
from qbraid.transforms.qasm3.compat import transform_notation_to_external

braket_circuits = LazyLoader("braket_circuits", globals(), "braket.circuits")
braket_openqasm = LazyLoader("braket_openqasm", globals(), "braket.ir.openqasm")

if TYPE_CHECKING:
    import braket.circuits


def qasm3_to_braket(qasm3_str: str) -> "braket.circuits.Circuit":
    """Converts an OpenQASM 3.0 string to a ``braket.circuits.Circuit``.

    Args:
        qasm3_str: OpenQASM 3 string

    Returns:
        The Amazon Braket circuit equivalent to the input OpenQASM 3.0 string

    Raises:
        CircuitConversionError: If qasm to braket conversion fails

    """
    qasm3_str = transform_notation_to_external(qasm3_str)

    try:
        program = braket_openqasm.Program(source=qasm3_str)
        return braket_circuits.Circuit.from_ir(source=program.source, inputs=program.inputs)
    except Exception as err:
        raise QasmError("Error converting qasm3 string to braket circuit") from err

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
Module for conversions from QASM 2 to Cirq Circuits

"""
from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.passes.qasm2 import flatten_qasm_program
from qbraid.programs.exceptions import QasmError
from qbraid.transpiler.annotations import weight

cirq_qasm_import = LazyLoader("cirq_contrib", globals(), "cirq.contrib.qasm_import")
cirq_qasm_parser = LazyLoader(
    "cirq_qasm_parser", globals(), "qbraid.transpiler.conversions.qasm2.cirq_qasm_parser"
)

if TYPE_CHECKING:
    import cirq


@weight(1)
def qasm2_to_cirq(qasm: str) -> "cirq.Circuit":
    """Returns a Cirq circuit equivalent to the input QASM string.

    Args:
        qasm: QASM string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input QASM string.
    """
    try:
        qasm = flatten_qasm_program(qasm)
        return cirq_qasm_parser.QasmParser().parse(qasm).circuit
    except cirq_qasm_import.QasmException as err:
        raise QasmError from err

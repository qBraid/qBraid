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
Module for conversions from QASM 2 to Cirq Circuits

"""
import cirq
from cirq.contrib.qasm_import.exception import QasmException as CirqQasmException

from qbraid.programs.exceptions import QasmError as QbraidQasmError
from qbraid.transforms.qasm2 import flatten_qasm_program

from .cirq_qasm_parser import QasmParser

QASMType = str


def qasm2_to_cirq(qasm: QASMType) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input QASM string.

    Args:
        qasm: QASM string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input QASM string.
    """
    try:
        qasm = flatten_qasm_program(qasm)
        return QasmParser().parse(qasm).circuit
    except CirqQasmException as err:
        raise QbraidQasmError from err

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
Module for performing QASM program checks before conversion

"""
from openqasm3.parser import QASM3ParsingError, parse

from ._qprogram import QPROGRAM_LIBS
from .exceptions import QasmError


def get_qasm_version(qasm_str: str) -> str:
    """Gets OpenQASM program version, either qasm2 or qasm3.

    Args:
        qasm_str: An OpenQASM program string

    Returns:
        QASM version from list :obj:`~qbraid.QPROGRAM_LIBS`

    Raises:
        :class:`~qbraid.QasmError`: If string does not represent a valid OpenQASAM program.

    """
    try:
        program = parse(qasm_str)
        verion = int(float(program.version))
        return f"qasm{verion}"
    except QASM3ParsingError as err:
        raise QasmError("Failed to parse OpenQASM program.") from err


def is_valid_qasm2(qasm_str: str) -> bool:
    """Checks if input string is a valid OpenQASM 2 program.

    NOTE: This should actually go in programs as a way to validate input qasm2 strings.

    Args:
        qasm_str: An OpenQASM program string

    Returns:
        bool: True if input string is a valid OpenQASM 2 program, False otherwise

    """
    if "qiskit" not in QPROGRAM_LIBS:
        return "OPENQASM 2" in qasm_str

    # pylint: disable=import-outside-toplevel
    from qiskit import QuantumCircuit
    from qiskit.qasm2 import QASM2ParseError

    try:
        _ = QuantumCircuit.from_qasm_str(qasm_str)
    except QASM2ParseError:
        return False
    return True

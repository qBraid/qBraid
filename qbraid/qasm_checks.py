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

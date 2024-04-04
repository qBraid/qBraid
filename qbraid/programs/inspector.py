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
from typing import TYPE_CHECKING, Optional

from openqasm3.parser import QASM3ParsingError, parse

from ._import import QPROGRAM_LIBS
from .exceptions import PackageValueError, ProgramTypeError, QasmError

if TYPE_CHECKING:
    import qbraid.programs


def get_qasm_version(qasm_str: str) -> str:
    """Gets OpenQASM program version, either qasm2 or qasm3.

    Args:
        qasm_str: An OpenQASM program string

    Returns:
        QASM version from list :obj:`~qbraid.programs.QPROGRAM_LIBS`

    Raises:
        :class:`~qbraid.programs.QasmError`: If string does not represent a valid OpenQASAM program.

    """
    qasm_str = qasm_str.replace("opaque", "// opaque")

    try:
        program = parse(qasm_str)
        verion = int(float(program.version))
        return f"qasm{verion}"
    except QASM3ParsingError as err:
        raise QasmError("Failed to parse OpenQASM program.") from err


def get_program_type(
    program: "qbraid.programs.QPROGRAM", require_supported: bool = True
) -> Optional[str]:
    """
    Get the type of a quantum program.

    Args:
        program (qbraid.programs.QPROGRAM): The quantum program to get the type of.
        require_supported (bool): If True, raise an error if the program type is not supported.

    Returns:
        str: The type of the quantum program, or None if the type cannot be determined and
             require_supported is False.
    """
    if isinstance(program, str):
        try:
            package = get_qasm_version(program)
        except QasmError as err:
            if require_supported:
                raise ProgramTypeError(
                    "Input of type string must represent a valid OpenQASM program."
                ) from err
            package = None

    else:
        try:
            program_module = program.__module__
            package = program_module.split(".")[0].lower()
        except AttributeError as err:
            if require_supported:
                raise ProgramTypeError(program) from err
            package = None

    if package not in QPROGRAM_LIBS and require_supported:
        raise PackageValueError(package)

    return package

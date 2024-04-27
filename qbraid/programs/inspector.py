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
from typing import TYPE_CHECKING, Optional, Type

from openqasm3.parser import QASM3ParsingError, parse

from .exceptions import PackageValueError, ProgramTypeError, QasmError
from .registry import QPROGRAM_REGISTRY, get_type_alias

if TYPE_CHECKING:
    import qbraid.programs


def find_str_type_alias(registry: dict[str, Type] = QPROGRAM_REGISTRY) -> Optional[str]:
    """Find additional keys with type 'str' in the registry."""
    str_keys = [k for k, v in registry.items() if v == str and k not in ("qasm2", "qasm3")]

    if len(str_keys) == 0:
        return None
    if len(str_keys) == 1:
        return str_keys[0]
    raise ValueError(f"Multiple additional keys with type 'str' found: {str_keys}")


def get_qasm_version(qasm_str: str) -> str:
    """Gets OpenQASM program version, either qasm2 or qasm3.

    Args:
        qasm_str: An OpenQASM program string

    Returns:
        QASM version from list :obj:`~qbraid.programs.QPROGRAM_ALIASES`

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
            package = find_str_type_alias()
            if package is None and require_supported:
                raise ProgramTypeError(
                    message="Input of type string must represent a valid OpenQASM program."
                ) from err

    else:
        try:
            package = get_type_alias(program)
        except ValueError as err:
            if require_supported:
                raise ProgramTypeError(program) from err
            package = None

    program_type = QPROGRAM_REGISTRY.get(package, None)

    if program_type is None:
        if require_supported:
            raise PackageValueError(package)
        return package

    if (
        not isinstance(program, program_type)
        and not isinstance(program, type(program_type))
        and require_supported
    ):
        raise ProgramTypeError(
            message=(
                f"Program of type '{type(program)}' does not match expected type "
                f"mapping '{program_type}' for derived alias '{package}'."
            )
        )

    return package

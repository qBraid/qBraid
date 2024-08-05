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
Module for managing and retrieving custom program type aliases

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type

from openqasm3.parser import QASM3ParsingError, parse

from .exceptions import ProgramTypeError, QasmError
from .registry import QPROGRAM_REGISTRY, QPROGRAM_TYPES

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


def parse_qasm_type_alias(qasm: str) -> str:
    """Gets OpenQASM program version, either qasm2 or qasm3.

    Args:
        qasm_str: An OpenQASM program string

    Returns:
        QASM version from list :obj:`~qbraid.programs.QPROGRAM_ALIASES`

    Raises:
        :class:`~qbraid.programs.QasmError`: If string does not represent a valid OpenQASAM program.

    """
    qasm = qasm.replace("opaque", "// opaque")

    try:
        program = parse(qasm)
    except QASM3ParsingError as err:
        raise QasmError("Failed to parse OpenQASM program.") from err

    verion = int(float(program.version))
    return f"qasm{verion}"


def _get_program_type_alias(program: qbraid.programs.QPROGRAM) -> str:
    """
    Get the type alias of a quantum program from registry.

    Args:
        program (qbraid.programs.QPROGRAM): The quantum program to get the type of.

    Returns:
        str: The type of the quantum program.

    Raises:
        ProgramTypeError: If the program type does not match any registered program types.
    """
    if isinstance(program, type):
        raise ProgramTypeError(message="Expected an instance of a quantum program, not a type.")

    if isinstance(program, str):
        try:
            return parse_qasm_type_alias(program)
        except QasmError as err:
            package = find_str_type_alias()
            if package is not None:
                return package
            raise ProgramTypeError(
                message=(
                    "Input of program of type string does not represent a valid OpenQASM program, "
                    "and no additional string type aliases are registered."
                )
            ) from err

    matched = []
    for alias, program_type in QPROGRAM_REGISTRY.items():
        if isinstance(program, (program_type, type(program_type))):
            matched.append(alias)

    if len(matched) == 1:
        return matched[0]

    if len(matched) > 1:
        raise ProgramTypeError(
            message=(
                f"Program of type '{type(program)}' matches multiple registered program types: "
                f"{matched}."
            )
        )

    raise ProgramTypeError(
        message=(
            f"Program of type '{type(program)}' does not match any registered "
            f"program types. Registered program types are: {QPROGRAM_TYPES}."
        )
    )


def get_program_type_alias(program: qbraid.programs.QPROGRAM, safe: bool = False) -> Optional[str]:
    """
    Get the type alias of a quantum program from registry.

    Args:
        program (qbraid.programs.QPROGRAM): The quantum program to get the type of.
        safe (bool): If True, return None if the program type does not match any registered
                     program types. Defaults to False.

    Returns:
        str: The type of the quantum program.
        None: If the program type does not match any registered program types and safe is True.

    Raises:
        ProgramTypeError: If the program type does not match any registered program types.
    """
    try:
        return _get_program_type_alias(program)
    except ProgramTypeError as err:
        if safe:
            return None
        raise err

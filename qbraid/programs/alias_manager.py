# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module for managing and retrieving custom program type aliases

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type

from .exceptions import ProgramTypeError
from .exceptions import QasmError as QbraidQasmError
from .registry import QPROGRAM_REGISTRY, QPROGRAM_TYPES
from .typer import IonQDict, get_qasm_type_alias

if TYPE_CHECKING:
    import qbraid.programs


def find_str_type_alias(registry: dict[str, Type] = QPROGRAM_REGISTRY) -> Optional[str]:
    """Find additional keys with type 'str' in the registry."""
    str_keys = [
        k for k, v in registry.items() if v is str and k not in ("qasm2", "qasm3", "qasm2_kirin")
    ]

    if len(str_keys) == 0:
        return None
    if len(str_keys) == 1:
        return str_keys[0]
    raise ValueError(f"Multiple additional keys with type 'str' found: {str_keys}")


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
            return get_qasm_type_alias(program)
        except QbraidQasmError as err:
            package = find_str_type_alias()
            if package is not None:
                return package
            raise ProgramTypeError(
                message=(
                    "Input of program of type string does not represent a valid OpenQASM program, "
                    "and no additional string type aliases are registered."
                )
            ) from err

    if isinstance(program, IonQDict):
        return IonQDict.__alias__

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

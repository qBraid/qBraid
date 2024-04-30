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
Module for registering custom program types and aliases

"""
from typing import Any, Optional, Type, Union

from ._import import _QPROGRAM_ALIASES, _QPROGRAM_REGISTRY, _QPROGRAM_TYPES, NATIVE_REGISTRY

QPROGRAM = Union[tuple(_QPROGRAM_TYPES)]
QPROGRAM_REGISTRY = _QPROGRAM_REGISTRY
QPROGRAM_ALIASES = _QPROGRAM_ALIASES
QPROGRAM_TYPES = _QPROGRAM_TYPES


def derive_program_type_alias(program_type: Type[Any]) -> str:
    """
    Determines an alias for the given program type based on its module or class name.

    Args:
        program_type (Type[Any]): The class or type for which to determine the alias.

    Returns:
        str: The determined alias for the program type.

    Raises:
        ValueError: If the alias cannot be automatically determined.
    """
    try:
        alias = program_type.__module__.split(".")[0]
        if alias in ["__main__", "builtins"]:
            alias = program_type.__name__
        return alias.lower()
    except (AttributeError, IndexError, TypeError) as err:
        raise ValueError(
            "Failed to automatically determine an alias from the program type's module."
        ) from err


def register_program_type(
    program_type: Type[Any], alias: Optional[str] = None, overwrite: bool = False
) -> None:
    """
    Registers a user-defined program type under the specified alias.

    Args:
        program_type (Type[Any]): The actual Python type or a callable that returns a type.
                             This can be a built-in type like str, a class, or any callable.
        alias (optional, str): The alias to register the program type under.
        overwrite (optional, bool): Whether to overwrite an existing alias with the new type.

    Raises:
        ValueError: If the alias is already registered with a different type,
                    if the program type is already registered under a different alias,
                    or if trying to register more than one additional 'str' type beyond
                    'qasm2' and 'qasm3'.
    """
    if not alias:
        alias = derive_program_type_alias(program_type)

    normalized_alias = alias.lower()

    # Check if the alias is already used and if it maps to a different type
    if normalized_alias in QPROGRAM_REGISTRY:
        if QPROGRAM_REGISTRY[normalized_alias] != program_type and overwrite is False:
            raise ValueError(f"Alias '{alias}' is already registered with a different type.")

    # Check if the type is already registered under any other alias
    existing_alias = next((k for k, v in QPROGRAM_REGISTRY.items() if v == program_type), None)
    if existing_alias and existing_alias != normalized_alias and overwrite is False:
        if program_type == str:
            str_types = [
                k for k, v in QPROGRAM_REGISTRY.items() if v == str and k not in ("qasm2", "qasm3")
            ]
            if (
                len(str_types) >= 1
                and normalized_alias not in str_types
                and normalized_alias not in ("qasm2", "qasm3")
            ):
                raise ValueError(
                    "Cannot register more than one additional 'str' type beyond 'qasm2', 'qasm3'."
                )
        else:
            raise ValueError(
                f"Program type '{program_type}' already registered under alias '{existing_alias}'."
            )

    # Register the new type and alias
    QPROGRAM_REGISTRY[normalized_alias] = program_type
    QPROGRAM_ALIASES.add(normalized_alias)
    QPROGRAM_TYPES.add(program_type)


def is_registered_alias_native(alias: str) -> bool:
    """
    Determine if the registered program type for a given alias matches the native program type.

    Args:
        alias (str): The alias to check against the native and registered program types.

    Returns:
        bool: True if the alias is registered and its program type matches the native type,
              otherwise False.
    """
    native_type = NATIVE_REGISTRY.get(alias)
    registered_type = QPROGRAM_REGISTRY.get(alias)

    return native_type is not None and native_type == registered_type

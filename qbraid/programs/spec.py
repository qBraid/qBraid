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
Module defining base program type specification

"""
from typing import Any, Optional, Type

from .registry import derive_program_type_alias, is_registered_alias_native, register_program_type


class ProgramSpec:
    """Base class used to register program type and type alias."""

    def __init__(
        self,
        program_type: Type[Any],
        alias: Optional[str] = None,
        overwrite: bool = False,
    ):
        self._program_type = program_type

        register_program_type(program_type, alias=alias, overwrite=overwrite)
        self._alias = alias or derive_program_type_alias(program_type)
        self._native = is_registered_alias_native(self._alias)

    @property
    def program_type(self) -> Type[Any]:
        """Return the registered program type."""
        return self._program_type

    @property
    def alias(self) -> str:
        """Return the alias of the registered program type."""
        return self._alias

    @property
    def native(self) -> bool:
        """True if program is natively supported by qBraid, False otherwise."""
        return self._native

    def __str__(self) -> str:
        return f"ProgramSpec({self._program_type.__name__}, {self.alias})"

    def __repr__(self) -> str:
        return (
            f"<ProgramSpec('{self._program_type.__module__}.{self._program_type.__name__}', "
            f"'{self.alias}')>"
        )

    def __eq__(self, other: object) -> bool:
        """
        Compare this ProgramSpec object with another object for equality based on type and alias.

        Args:
            other (object): Another object to compare against.

        Returns:
            bool: True if both objects are instances of ProgramSpec and have the
                  same type and alias, False otherwise.
        """
        if not isinstance(other, ProgramSpec):
            return False

        this_spec = (self._program_type, self._alias, self._native)
        other_spec = (other._program_type, other._alias, other._native)
        return this_spec == other_spec

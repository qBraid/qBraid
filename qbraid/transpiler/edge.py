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
Module for defining custom conversions

"""
import inspect
from typing import TYPE_CHECKING, Any, Callable, Union

from qbraid.programs import SUPPORTED_QPROGRAMS, get_program_type

if TYPE_CHECKING:
    import qbraid


class Conversion:
    """
    Class for defining and handling custom conversions between different quantum program packages.

    """

    def __init__(self, source: str, target: str, conversion_func: Callable):
        """
        Initialize a Conversion instance with source and target packages and a conversion function.

        Args:
            source (str): The source package from which conversion starts.
            target (str): The target package to which conversion is done.
            conversion_func (Callable): The function that performs the actual conversion.
        """
        self._source = source
        self._target = target
        self._conversion_func = conversion_func
        self._native = self._is_native()

    @property
    def source(self) -> str:
        """
        The source package of the conversion.

        Returns:
            str: The source package name.
        """
        return self._source

    @property
    def target(self) -> str:
        """
        The target package of the conversion.

        Returns:
            str: The target package name.
        """
        return self._target

    @property
    def native(self) -> bool:
        """
        True if the conversion function is native to qbraid package, False otherwise.

        Returns:
            bool: Whether the conversion function is native to qbraid package.
        """
        return self._native

    def _is_native(self) -> bool:
        """
        Check if a conversion function is native to qbraid package.

        Args:
            func (Callable): The conversion function to check.

        Returns:
            bool: True if the function is native, False otherwise.
        """
        module = inspect.getmodule(self._conversion_func)

        if module is None:
            return False

        package = module.__name__.split(".")[0]
        return package == "qbraid"

    def convert(
        self, program: "qbraid.programs.QPROGRAM"
    ) -> Union["qbraid.programs.QPROGRAM", Any]:
        """
        Convert a quantum program from the source package to the target package.

        Args:
            program (qbraid.programs.QPROGRAM): The quantum program to be converted.

        Returns:
            Union[qbraid.programs.QPROGRAM, Any]: The converted quantum program,
                                         typically of a supported program type.

        Raises:
            ValueError: If the provided program's type does not match the source package type.
        """
        package = get_program_type(program)
        if package != self._source:
            raise ValueError(
                f"Expected program of type {SUPPORTED_QPROGRAMS[self._source]}, "
                f"but got program of type {SUPPORTED_QPROGRAMS[package]}."
            )
        return self._conversion_func(program)

    def __repr__(self) -> str:
        """
        Represent the Conversion instance as a string indicating
        source and target packages.

        Returns:
            str: String representation of the Conversion instance.
        """
        return f"('{self._source}', '{self._target}')"

    def __eq__(self, other: Any) -> bool:
        """
        Check if another instance is equal to this instance.

        Args:
            other (Any): Another instance to compare.

        Returns:
            bool: True if the instances are equal, False otherwise.
        """
        if not isinstance(other, Conversion):
            return False

        return (
            self._source == other._source
            and self._target == other._target
            and self._native == other._native
        )

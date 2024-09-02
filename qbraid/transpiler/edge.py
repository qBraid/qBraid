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
Module for defining custom conversions

"""
from __future__ import annotations

import importlib.util
import inspect
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import numpy as np

from qbraid.programs import QPROGRAM_REGISTRY, get_program_type_alias

if TYPE_CHECKING:
    import qbraid.programs


class Conversion:
    """
    Class for defining and handling custom conversions between different quantum program packages.

    """

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        source: str,
        target: str,
        conversion_func: Callable,
        weight: Optional[float] = None,
        bias: Optional[float] = None,
    ):
        """
        Initialize a Conversion instance with source and target packages and a conversion function.

        Args:
            source (str): The source package from which conversion starts.
            target (str): The target package to which conversion is done.
            conversion_func (Callable): The function that performs the actual conversion.
            weight (Optional[float]): Optional weighting factor for the conversion, ranging [0,1].
                If not specified, defaults to 1 or a custom value derived from the conversion_func.
            bias (Optional[float]): Optional factor used to fine-tune the weight calculation and
                modify the decision thresholds for pathfinding. Defaults to 0. Higher values
                prioritize shorter paths. For example, a bias of 0.25 slightly favors a single
                conversion at weight 0.8 over two conversions at weight 1.0, whereas a bias of 0.1
                requires a single conversion of weight > 0.9 to be preferred over two at weight 1.0.
        """
        self._source = source
        self._target = target
        self._conversion_func = conversion_func
        self._bias = bias if bias is not None else 0
        self._weight = self._get_adjusted_weight(weight)
        self._extras = getattr(conversion_func, "requires_extras", [])
        self._native = self._is_module_native(conversion_func)
        self._supported = self._is_conversion_supported()

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

    @property
    def supported(self) -> bool:
        """
        True if all packages required to perform the conversion are installed. False otherwise.

        Returns:
            bool: Whether the conversion function supported in the current runtime environment.
        """
        return self._supported

    @property
    def weight(self) -> int:
        """
        The weight of the conversion function used to prioritize conversion paths.

        Returns:
            int: The weight of the conversion function.
        """
        return self._weight

    def _get_adjusted_weight(self, weight: Optional[float] = None) -> float:
        """
        Calculates and returns the effective weight of the conversion, applying a bias to
        prioritize shorter conversion paths when used with pathfinding algorithms like rustworkx.

        Args:
            weight (float, optional): The initial weight provided by the user. Defaults to
                the weight attribute of conversion_func if not provided.

        Returns:
            float: The calculated weight adjusted for pathfinding optimization.

        Raises:
            ValueError: If the calculated or provided weight is not between 0 and 1, inclusive.
        """
        effective_weight = (
            weight if weight is not None else getattr(self._conversion_func, "weight", 1)
        )

        if not 0 <= effective_weight <= 1:
            raise ValueError("Weight must be a float between 0 and 1, inclusive.")

        # Invert and log transform for positive weight differentiation with rustworkx
        rx_adjusted_weight = float("inf") if effective_weight == 0 else np.log(1 / effective_weight)

        adjusted_weight = rx_adjusted_weight + self._bias

        return adjusted_weight

    def _is_module_native(self, func: Callable) -> bool:
        """
        Determine if the function's module is 'qbraid' and requires no extras.

        Args:
            func (Callable): The function to check the module of.

        Returns:
            bool: True if the module is 'qbraid' and requires no extras, False otherwise.
        """
        module = inspect.getmodule(func)
        is_native = (
            module is not None
            and module.__name__.split(".")[0] == "qbraid"
            and len(self._extras) == 0
            and getattr(func, "weight", None) is not None
        )
        return is_native

    def _is_conversion_supported(self) -> bool:
        """
        Determine if the required packages for the conversion are installed.

        Returns:
            bool: True if supported, otherwise False.
        """
        if self._native:
            return True
        return all(importlib.util.find_spec(m) is not None for m in self._extras)

    def convert(self, program: qbraid.programs.QPROGRAM) -> Union[qbraid.programs.QPROGRAM, Any]:
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
        package = get_program_type_alias(program)
        if package != self._source:
            raise ValueError(
                f"Expected program of type {QPROGRAM_REGISTRY[self._source]}, "
                f"but got program of type {QPROGRAM_REGISTRY[package]}."
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
            and self._supported == other._supported
            and self._extras == other._extras
            and self._weight == other._weight
        )

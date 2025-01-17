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
Module defining function annotations (e.g. decorators) used in the transpiler.

"""

from functools import wraps
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def requires_extras(*packages: str) -> Callable[[F], F]:
    """
    Decorator factory to mark conversion functions that require additional dependencies
    beyond their "{source}_to_{target}" naming convention. It adds specified dependencies
    as attributes to the function.

    Args:
        *packages: The names of the required additional dependencies.

    Returns:
        Callable: A decorator that marks a function with the required dependencies.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        setattr(wrapper, "requires_extras", list(packages))
        return cast(F, wrapper)

    return decorator


def weight(value: float) -> Callable[[F], F]:
    """
    Decorator factory to mark conversion functions with a weight attribute.
    This weight attribute is used to prioritize conversion paths in a conversion graph.

    Args:
        value (float): The weight of the conversion function. Must be between 0 and 1 inclusive.

    Returns:
        Callable: A decorator that assigns the specified weight to a function.
    """
    if not 0 <= value <= 1:
        raise ValueError("Weight value must be between 0 and 1.")

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        setattr(wrapper, "weight", value)
        return cast(F, wrapper)

    return decorator

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

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
Module for managing conversion configurations for quantum runtime.

"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    import qbraid.transpiler


@dataclass
class ConversionScheme:
    """
    A data class for managing conversion configurations for quantum device operations.

    Attributes:
        conversion_graph (Optional[ConversionGraph]): Graph coordinating conversions between
            different quantum software program types. If None, the default qBraid graph is used.
        max_path_attempts (int): The maximum number of conversion paths to attempt before
            raising an exception. Defaults to 3.
        max_path_depth (Optional[int]): The maximum depth of conversions within a given path to
            allow. A depth of 2 would allow a conversion path like ['cirq' -> 'qasm2' -> 'qiskit'].
            Defaults to None, meaning no limit.
        extra_kwargs (dict[str, Any]): A dictionary to hold any additional keyword arguments that
            users want to pass to the transpile function at runtime.

    Methods:
        to_dict: Converts the conversion scheme to a flat dictionary suitable for passing as kwargs.
        update_values: Dynamically updates the values of the instance's attributes.
    """

    conversion_graph: Optional[qbraid.transpiler.ConversionGraph] = None
    max_path_attempts: int = 3
    max_path_depth: Optional[int] = None
    extra_kwargs: dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        kwargs_str = ", ".join(f"{key}={value}" for key, value in self.extra_kwargs.items())
        return (
            f"ConversionScheme(conversion_graph={self.conversion_graph}, "
            f"max_path_attempts={self.max_path_attempts}, "
            f"max_path_depth={self.max_path_depth}, "
            f"{kwargs_str})"
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the ConversionScheme fields to a flat dictionary suitable for passing as kwargs.

        Returns:
            A dictionary with all fields ready to be passed as keyword arguments,
            including nested extra_kwargs.
        """
        scheme = asdict(self)
        scheme.update(scheme.pop("extra_kwargs", {}))
        scheme.update({"conversion_graph": self.conversion_graph})
        return scheme

    def update_values(self, **kwargs) -> None:
        """
        Updates the attributes of the conversion scheme with new values provided
        as keyword arguments.

        Args:
            **kwargs: Arbitrary keyword arguments containing attribute names and their new values.

        Raises:
            AttributeError: If a provided attribute name does not exist.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"{key} is not a valid attribute of ConversionScheme")

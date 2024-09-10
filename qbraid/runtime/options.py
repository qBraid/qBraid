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
Module for managing qBraid-specific runtime options.

"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, Callable


@dataclass
class Options:
    """
    Manages qBraid-specific options with controlled defaults and dynamic fields.
    Allows default fields to be modified and arbitrary additional fields to be added.

    """

    transpile: bool = True
    transform: bool = True
    verify: bool = True

    _validators: dict[str, Callable[[Any], bool]] = dataclass_field(
        default_factory=dict, repr=False
    )

    def __init__(self, **kwargs: Any):
        self.transpile = kwargs.pop("transpile", True)
        self.transform = kwargs.pop("transform", True)
        self.verify = kwargs.pop("verify", True)

        self._fields = kwargs

    def set_validator(self, option_name: str, validator: Callable[[Any], bool]):
        """Sets a validator for a specific field."""
        if not hasattr(self, option_name) and option_name not in self._fields:
            raise KeyError(f"Field '{option_name}' is not present in options.")
        self._validators[option_name] = validator

    def validate(self, option_name: str, value: Any):
        """Validates a field's value using the registered validator, if any."""
        validator = self._validators.get(option_name)
        if validator and not validator(value):
            raise ValueError(f"Value {value} is not valid for field '{option_name}'.")

    def update_options(self, **new_options):
        """Updates multiple options with validation."""
        for option_name, value in new_options.items():
            if hasattr(self, option_name):
                self.validate(option_name, value)
                setattr(self, option_name, value)
            else:
                self._fields[option_name] = value

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-like access."""
        if hasattr(self, key):
            return getattr(self, key)
        return self._fields[key]

    def __setitem__(self, key: str, value: Any):
        """Allow dictionary-like updates."""
        self.update_options(**{key: value})

    def __delitem__(self, key: str):
        """Prevent deletion of default fields but allow deletion of additional fields."""
        if hasattr(self, key):
            raise KeyError(f"Cannot delete default option '{key}'.")
        if key in self._fields:
            del self._fields[key]
        else:
            raise KeyError(f"Field '{key}' not found in options.")

    def __getattr__(self, name: str) -> Any:
        """Access options like attributes."""
        if name in self._fields:
            return self._fields[name]
        raise AttributeError(f"Option '{name}' is not defined.")

    def __setattr__(self, name: str, value: Any):
        """Set options like attributes, ensuring validation if necessary."""
        if name in {"transpile", "transform", "verify", "_fields", "_validators"}:
            super().__setattr__(name, value)
        else:
            self.update_options(**{name: value})

    def __repr__(self):
        """Returns a string representation of the options."""
        base_options = {k: getattr(self, k) for k in ["transpile", "transform", "verify"]}
        return f"Options({base_options}, additional={self._fields})"

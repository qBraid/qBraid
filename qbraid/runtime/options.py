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

import copy
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, Callable


@dataclass
class RuntimeOptions:
    """
    Manages qBraid-specific options with controlled defaults and dynamic fields.

    The `RuntimeOptions` class allows you to initialize options with default fields,
    add dynamic fields, and validate the values of specific fields using custom
    validators. It also provides dictionary-like access to option fields.

    Example:

    .. code-block:: python

        >>> from qbraid.runtime.options import RuntimeOptions

        # Initialize options with default and custom fields
        >>> options = RuntimeOptions(check=True, custom_field=42)

        # Access option fields like dictionary
        >>> options["check"]
        True

        # Add dynamic fields
        >>> options["new_field"] = "hello"
        >>> print(options)
        RuntimeOptions(check=True, custom_field=42, new_field='hello')

        # Set a validator for a field
        >>> options.set_validator("check", lambda x: isinstance(x, bool))

        # Attempting to set an invalid value will raise a ValueError
        >>> options.check = False  # Valid
        >>> options.check = "invalid_value"  # Raises ValueError

        # Make a shallow copy of the options
        >>> options_copy = copy.copy(options)
        >>> print(options_copy)
        RuntimeOptions(check=False, custom_field=42, new_field='hello')

    Args:
        kwargs: Keyword arguments representing the initial options to set.
                These will form the default fields of the `Options` instance.

    Attributes:
        _fields (dict): The internal dictionary storing option fields.
        _validators (dict): A dictionary storing field validators.

    """

    _validators: dict[str, Callable[[Any], bool]] = dataclass_field(
        default_factory=dict, repr=False
    )

    def __init__(self, **kwargs: Any):
        reserved_keywords = {"set_validator", "validate_option", "update_options", "get"}

        for key in kwargs:
            if key in reserved_keywords:
                raise ValueError(f"The option name '{key}' is reserved and cannot be used.")
            if key.startswith("__"):
                raise ValueError(f"The option name '{key}' with dunder prefix is not allowed.")

        object.__setattr__(self, "_default_fields", kwargs.copy())
        object.__setattr__(self, "_fields", kwargs.copy())
        object.__setattr__(self, "_validators", {})

    def set_validator(self, option_name: str, validator: Callable[[Any], bool]):
        """Sets a validator for a specific field."""
        if not hasattr(self, option_name) and option_name not in self._fields:
            raise KeyError(f"Field '{option_name}' is not present in options.")
        self._validators[option_name] = validator

    def validate_option(self, option_name: str, value: Any):
        """Validates a field's value using the registered validator, if any.

        Raises:
            ValueError: If the validator function raises an exception or returns False.
        """
        validator = self._validators.get(option_name)
        if validator:
            try:
                is_valid = validator(value)
            except Exception as err:
                raise ValueError(
                    f"Validator for field '{option_name}' raised an exception: {err}"
                ) from err
            if not is_valid:
                raise ValueError(f"Value '{value}' is not valid for field '{option_name}'.")

    def update_options(self, **new_options):
        """Updates multiple options with validation."""
        for option_name, value in new_options.items():
            if hasattr(self, option_name):
                self.validate_option(option_name, value)
                setattr(self, option_name, value)
            else:
                self._fields[option_name] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for the given key, or the default value if not found."""
        if hasattr(self, key):
            return getattr(self, key)
        return self._fields.get(key, default)

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
        if key in self._default_fields:
            raise KeyError(f"Cannot delete default field '{key}'.")
        if key in self._fields:
            del self._fields[key]
        else:
            raise KeyError(f"Field '{key}' not found in options.")

    def __getattr__(self, name: str) -> Any:
        """Access options like attributes."""
        if name in {"_fields", "_default_fields", "_validators"}:
            return self.__dict__.get(name)
        if name in self._fields:
            return self._fields[name]
        raise AttributeError(f"Option '{name}' is not defined.")

    def __setattr__(self, name: str, value: Any):
        """Set options like attributes, ensuring validation if necessary."""
        if name in {"_fields", "_default_fields", "_validators"}:
            super().__setattr__(name, value)
        elif name in self._fields or name in self._default_fields:
            if self._fields.get(name) != value:
                if name in self._validators:
                    self.validate_option(name, value)
                self._fields[name] = value
        else:
            self.update_options(**{name: value})

    @property
    def __dict__(self):
        """Returns the internal fields as a dictionary."""
        return self._fields

    def __iter__(self):
        """Allow iteration over the key-value pairs of the internal fields."""
        return iter(self._fields.items())

    def __len__(self):
        """Return the number of fields."""
        return len(self._fields)

    def __repr__(self):
        """Returns a string representation of the options."""
        options_str = ", ".join(f"{k}={v!r}" for k, v in self._fields.items())
        return f"RuntimeOptions({options_str})"

    def __copy__(self):
        """Create a shallow copy of the RuntimeOptions object."""
        cls = self.__class__
        new_instance = cls(**self._fields)
        new_instance._validators = copy.copy(self._validators)
        return new_instance

    def __eq__(self, other: Any) -> bool:
        """Custom equality check for RuntimeOptions objects."""
        if not isinstance(other, RuntimeOptions):
            return False
        if self._fields != other._fields:
            return False
        if set(self._validators.keys()) != set(other._validators.keys()):
            return False
        return True

    def merge(self, other: "RuntimeOptions", override_validators: bool = True):
        """Merges another RuntimeOptions instance into this one.

        Args:
            other (RuntimeOptions): The RuntimeOptions instance to merge from.
            override_validators (bool): Determines whether validators from `other`
                should override existing validators in `self`.

        Raises:
            ValueError: If any option value is invalid after merging.
        """
        combined_validators = self._validators.copy()
        if override_validators:
            combined_validators.update(other._validators)
        else:
            for key, validator in other._validators.items():
                combined_validators.setdefault(key, validator)

        combined_fields = self._fields.copy()
        combined_fields.update(other.__dict__)

        object.__setattr__(self, "_validators", combined_validators)
        object.__setattr__(self, "_fields", combined_fields)

        if override_validators:
            options_to_validate = combined_fields.items()
        else:
            options_to_validate = ((key, combined_fields[key]) for key in other.__dict__.keys())

        for option_name, value in options_to_validate:
            validator = combined_validators.get(option_name)
            if validator and not validator(value):
                raise ValueError(
                    f"Value '{value}' is not valid for field '{option_name}' after merging."
                )

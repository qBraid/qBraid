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
Module implementing a bidirectional dictionary.

"""


class BiDict:
    def __init__(self):
        """Initialize the bidirectional dictionary with two internal dictionaries."""
        self.key_to_value: dict = {}
        self.value_to_key: dict = {}

    def __str__(self) -> str:
        """Return the string representation of the key-to-value dictionary."""
        return str(self.key_to_value)

    def add(self, key, value, overwrite: bool = False) -> None:
        """
        Add a key-value pair to the bidirectional dictionary.

        Args:
            key: The key to add.
            value: The value to associate with the key.
            overwrite: A boolean flag that, if True, allows overwriting existing entries.

        Raises:
            ValueError: If the key or value already exists and overwrite is False.
        """
        if key in self.key_to_value:
            if overwrite:
                self.remove_by_key(key)
            else:
                raise ValueError(f"Key {key} already exists.")
        if value in self.value_to_key:
            if overwrite:
                self.remove_by_value(value)
            else:
                raise ValueError(f"Value {value} already exists.")
        self.key_to_value[key] = value
        self.value_to_key[value] = key

    def remove_by_key(self, key) -> None:
        """
        Remove the entry associated with the given key.

        Args:
            key: The key whose entry should be removed.
        """
        if key in self.key_to_value:
            value = self.key_to_value.pop(key)
            del self.value_to_key[value]

    def remove_by_value(self, value) -> None:
        """
        Remove the entry associated with the given value.

        Args:
            value: The value whose entry should be removed.
        """
        if value in self.value_to_key:
            key = self.value_to_key.pop(value)
            del self.key_to_value[key]

    def get_value(self, key):
        """
        Retrieve the value associated with a given key.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key, or None if the key does not exist.
        """
        return self.key_to_value.get(key)

    def get_key(self, value):
        """
        Retrieve the key associated with a given value.

        Args:
            value: The value to look up.

        Returns:
            The key associated with the value, or None if the value does not exist.
        """
        return self.value_to_key.get(value)

    def __contains__(self, key) -> bool:
        """Check if the key exists in the dictionary."""
        return key in self.key_to_value

    def __len__(self) -> int:
        """Return the number of entries in the dictionary."""
        return len(self.key_to_value)

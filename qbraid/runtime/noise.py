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
Module for representing various noise models for quantum simulators.

"""
import re
import threading
from collections.abc import MutableMapping
from dataclasses import dataclass, field
from typing import Iterator, Optional, Union


@dataclass(frozen=True)
class NoiseModel:
    """Class representing a single noise model."""

    # pylint: disable=line-too-long
    _defaults = {
        "ideal": "The simulation is performed without any noise, representing an ideal quantum computer.",
        "depolarizing": "Applies random errors to qubits, effectively turning a pure quantum state into a mixed state.",
        "amplitude_damping": "Simulates energy loss in a quantum system, causing qubits to decay from the excited state to the ground state.",
        "phase_damping": "Represents dephasing, where the relative phase between quantum states is randomized without energy loss.",
        "bit_flip": "Randomly flips the state of qubits (i.e., from 0 to 1 or from 1 to 0) with a certain probability.",
        "phase_flip": "Randomly flips the phase of a qubit state (i.e., it applies a Z gate) with a certain probability.",
    }
    # pylint: enable=line-too-long

    name: str = field(repr=False)
    description: Optional[str] = None
    _value: str = field(init=False)

    def __post_init__(self):
        normalized_value = self._normalize(self.name)
        object.__setattr__(self, "_value", normalized_value)
        description = self.description or self._defaults.get(normalized_value)
        self._validate(normalized_value, description)
        object.__setattr__(self, "description", description)

    @classmethod
    def _validate(cls, canonical_value: str, description: Optional[str] = None):
        if not re.match(r"^[\w\s\-_]+$", canonical_value):
            raise ValueError(
                f"Invalid noise model name: '{canonical_value}'. "
                "Allowed characters are letters, digits, spaces, hyphens, and underscores."
            )
        if description and len(description) > 120:
            raise ValueError("Description must be 120 characters or fewer.")

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[\s_]+", "_", value.strip().lower())

    def __str__(self):
        return self.value

    @property
    def value(self) -> str:
        """Normalized noise model name."""
        return self._value

    def __eq__(self, other):
        if isinstance(other, NoiseModel):
            return self.value == other.value and self.description == other.description
        if isinstance(other, str):
            return self.value == self._normalize(other)
        return NotImplemented

    def __hash__(self):
        return hash((self.value, self.description))

    def __repr__(self):
        return f"NoiseModel('{self.name}')"


class NoiseModelSet(MutableMapping):
    """Class managing a registry of noise models."""

    def __init__(self):
        self._models: dict[str, NoiseModel] = {}
        self._lock = threading.Lock()

    def add(self, name: str, description: Optional[str] = None, overwrite: bool = False):
        """Add a new noise model to the registry."""
        canonical_name = NoiseModel._normalize(name)
        new_model = NoiseModel(name, description)
        with self._lock:
            existing_model = self._models.get(canonical_name)
            if existing_model and not overwrite:
                if new_model != existing_model:
                    raise ValueError(
                        f"Noise model '{canonical_name}' already exists with a "
                        "different definition. Use overwrite=True to overwrite."
                    )
            self._models[canonical_name] = new_model

    def get(self, key: str, default: Optional[NoiseModel] = None) -> NoiseModel:
        """Retrieve a noise model by name."""
        canonical_name = NoiseModel._normalize(key)
        return self._models.get(canonical_name, default)

    def remove(self, name: str):
        """Remove a noise model from the registry."""
        canonical_name = NoiseModel._normalize(name)
        with self._lock:
            if canonical_name not in self._models:
                raise KeyError(f"Noise model '{name}' not found.")
            del self._models[canonical_name]

    def discard(self, name: str):
        """Remove a noise model if it exists; do nothing otherwise."""
        canonical_name = NoiseModel._normalize(name)
        with self._lock:
            self._models.pop(canonical_name, None)

    def clear(self):
        """Clear all noise models from the registry."""
        with self._lock:
            self._models.clear()

    def update(self, other: "NoiseModelSet"):  # pylint: disable=arguments-differ
        """Update the registry with another NoiseModelSet instance."""
        if isinstance(other, dict):
            other = NoiseModelSet.from_dict(other)
        elif not isinstance(other, NoiseModelSet):
            raise TypeError("Can only update from a dict or another NoiseModelSet instance.")
        with self._lock:
            with other._lock:
                self._models.update(other._models)

    def __getitem__(self, key: str) -> NoiseModel:
        noise_model = self.get(key)
        if noise_model is None:
            raise KeyError(f"Noise model {key} not found.")
        return noise_model

    def __setitem__(self, key: str, value: NoiseModel):
        if not isinstance(value, NoiseModel):
            raise ValueError("Value must be a NoiseModel instance.")
        canonical_name = NoiseModel._normalize(key)
        if canonical_name != value.value:
            raise ValueError("Key does not match the NoiseModel's normalized value.")
        with self._lock:
            self._models[canonical_name] = value

    def __delitem__(self, key: str):
        self.remove(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self._models)

    def __len__(self) -> int:
        return len(self._models)

    def __contains__(self, key: str) -> bool:
        if not isinstance(key, str):
            return False
        canonical_name = NoiseModel._normalize(key)
        return canonical_name in self._models

    def __repr__(self):
        return f"NoiseModelSet({list(self._models.keys())})"

    def values(self) -> Iterator[NoiseModel]:
        """Return an iterator over the noise models."""
        return iter(self._models.values())

    def items(self):
        """Return an iterator over the (name, noise model) pairs."""
        return self._models.items()

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "NoiseModelSet":
        """Create a NoiseModelSet instance from a dictionary."""
        models = cls()
        for name, description in data.items():
            models.add(name, description)
        return models

    @classmethod
    def from_iterable(cls, data: Union[list[str], set[str], tuple[str, ...]]) -> "NoiseModelSet":
        """Create a NoiseModelSet instance from a list, set, or tuple."""
        models = cls()
        for name in data:
            models.add(name)
        return models

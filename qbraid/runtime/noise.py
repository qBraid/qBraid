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
from typing import Optional


class NoiseModel:
    """Class representing various noise models for quantum simulators."""

    _noise_models = {
        "no_noise": "The simulation is performed without any noise, representing an ideal quantum computer.",
        "depolarizing": "Applies random errors to qubits, effectively turning a pure quantum state into a mixed state.",
        "amplitude_damping": "Simulates energy loss in a quantum system, causing qubits to decay from the excited state to the ground state.",
        "phase_damping": "Represents dephasing, where the relative phase between quantum states is randomized without energy loss.",
        "bit_flip": "Randomly flips the state of qubits (i.e., from 0 to 1 or from 1 to 0) with a certain probability.",
        "phase_flip": "Randomly flips the phase of a qubit state (i.e., it applies a Z gate) with a certain probability.",
        "other": "Placeholder for custom or unspecified noise models.",
    }

    _synonyms = {
        "ideal": "no_noise",
    }

    # Thread lock for thread-safe modifications
    _lock = threading.Lock()

    def __init__(self, value, description: Optional[str] = None):
        canonical_value = self.get_canonical_value(value)
        object.__setattr__(self, "_original_input", value)
        self._validate(canonical_value, description)
        object.__setattr__(self, "value", canonical_value)
        object.__setattr__(self, "_input", self._normalize(value))

        if description is None:
            description = self._noise_models.get(canonical_value)
        object.__setattr__(self, "description", description)

    @classmethod
    def _normalize(cls, value: str) -> str:
        return re.sub(r"[\s\-_]+", "_", value.strip().lower())

    @classmethod
    def get_canonical_value(cls, value):
        normalized = cls._normalize(value)
        return cls._synonyms.get(normalized, normalized)

    @classmethod
    def _validate(cls, canonical_value: str, description: str = None):
        if not re.match(r"^[\w\s\-_]+$", canonical_value):
            raise ValueError(
                f"Invalid noise model name: '{canonical_value}'. Allowed characters are letters, digits, spaces, hyphens, and underscores."
            )
        if description and len(description) > 120:
            raise ValueError("Description must be 120 characters or fewer.")

    def __repr__(self):
        return f"NoiseModel('{self._original_input}')"

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, NoiseModel):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == self.get_canonical_value(other)
        else:
            return False

    def __hash__(self):
        return hash(self.value)

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError(f"Cannot modify attribute '{name}' after initialization.")
        super().__setattr__(name, value)

    def copy(self):
        return NoiseModel(self._original_input, self.description)

    @classmethod
    def register(cls, name: str, description: Optional[str] = None, overwrite: bool = False):
        canonical_name = cls._normalize(name)
        canonical_name = cls._synonyms.get(canonical_name, canonical_name)

        cls._validate(canonical_name, description)

        with cls._lock:
            if canonical_name in cls._noise_models:
                if not overwrite:
                    raise ValueError(
                        f"Noise model '{canonical_name}' already exists. Use overwrite=True to overwrite."
                    )

            cls._noise_models[canonical_name] = description or cls._noise_models.get(
                canonical_name, ""
            )

        return cls(name, description)

    @classmethod
    def register_synonym(cls, synonym: str, canonical_name: str):
        """
        Register a synonym for an existing noise model.

        Args:
            synonym (str): The synonym to register.
            canonical_name (str): The canonical name of the existing noise model.

        Raises:
            ValueError: If the canonical name does not exist.
        """
        canonical_name_normalized = cls._normalize(canonical_name)
        synonym_normalized = cls._normalize(synonym)

        if canonical_name_normalized not in cls._noise_models:
            raise ValueError(f"Canonical noise model '{canonical_name}' does not exist.")

        with cls._lock:
            cls._synonyms[synonym_normalized] = canonical_name_normalized

    @classmethod
    def list_registered(cls):
        """List all registered canonical noise model names."""
        return list(cls._noise_models.keys())

    @classmethod
    def list_synonyms(cls):
        """List all registered synonyms and their canonical names."""
        return dict(cls._synonyms)

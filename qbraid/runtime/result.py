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
Module defining abstract QuantumJobResult Class

"""
from abc import ABC, abstractmethod
from typing import Any, Optional

import numpy as np


class QuantumJobResult(ABC):
    """Abstract interface for result-like classes.

    Args:
        _result: A result-like object

    """

    def __init__(self, result: Optional[Any] = None):
        self._result = result

    @abstractmethod
    def measurements(self) -> np.ndarray:
        """Return measurements as list"""

    @abstractmethod
    def raw_counts(self, **kwargs):
        """Returns raw histogram data of the run"""

    @staticmethod
    def format_counts(counts: dict, include_zero_values: bool = False) -> dict:
        """Formats, sorts, and adds missing bit indices to counts dictionary
        Can pass in a 'include_zero_values' parameter to decide whether to include the states
        with zero counts.

        For example:

        .. code-block:: python

            >>> counts
            {'1 1': 13, '0 0': 46, '1 0': 79}
            >>> QuantumJobResult.format_counts(counts)
            {'00': 46, '10': 79, '11': 13}
            >>> QuantumJobResult.format_counts(counts, include_zero_values=True)
            {'00': 46, '01': 0, '10': 79, '11': 13}

        """
        counts = {key.replace(" ", ""): value for key, value in counts.items()}

        num_bits = max(len(key) for key in counts)
        all_keys = [format(i, f"0{num_bits}b") for i in range(2**num_bits)]
        final_counts = {key: counts.get(key, 0) for key in sorted(all_keys)}

        if not include_zero_values:
            final_counts = {key: value for key, value in final_counts.items() if value != 0}

        return final_counts

    def measurement_counts(self, include_zero_values: bool = False, **kwargs) -> dict:
        """Returns the sorted histogram data of the run"""
        raw_counts = self.raw_counts(**kwargs)
        if isinstance(raw_counts, dict):
            return self.format_counts(raw_counts, include_zero_values=include_zero_values)
        return [
            self.format_counts(counts, include_zero_values=include_zero_values)
            for counts in raw_counts
        ]


class QbraidJobResult(QuantumJobResult):
    """Class to represent the results of a quantum circuit simulation."""

    def __init__(self, measurements: np.ndarray, execution_duration: Optional[int] = None):
        """Create a new Result object."""
        super().__init__()
        self._measurements = measurements
        self._execution_duration = execution_duration
        self._cached_histogram = None
        self._cached_metadata = None

    def measurements(self):
        """Return the measurement results 2D numpy array."""
        return self._measurements

    def raw_counts(self, decimal: bool = False, **kwargs):
        """Returns raw histogram data of the run"""
        counts = self._array_to_histogram(self.measurements())

        if decimal is True:
            counts = {int(key, 2): value for key, value in counts.items()}

        return counts

    def measurement_probabilities(self, **kwargs) -> dict[str, float]:
        """Calculate and return the probabilities of each measurement result."""
        counts = self.measurement_counts(**kwargs)
        probabilities = self.counts_to_probabilities(counts)
        return probabilities

    def _array_to_histogram(self, arr: np.ndarray) -> dict[str, int]:
        """Implement caching mechanism here."""
        if self._cached_histogram is None:
            row_strings = ["".join(map(str, row)) for row in arr]
            self._cached_histogram = {row: row_strings.count(row) for row in set(row_strings)}
        return self._cached_histogram

    @staticmethod
    def counts_to_probabilities(counts: dict[str, int]) -> dict[str, float]:
        """
        Convert histogram counts to probabilities.

        Args:
            counts (Dict[str, int]): A dictionary with measurement outcomes as keys and
                                     their counts as values.

        Returns:
            Dict[str, float]: A dictionary with measurement outcomes as keys and their
                              probabilities as values.
        """
        total_counts = sum(counts.values())
        measurement_probabilities = {
            outcome: count / total_counts for outcome, count in counts.items()
        }
        return measurement_probabilities

    def metadata(self) -> dict[str, int]:
        """Return metadata about the measurement results."""
        if self._cached_metadata is None:
            num_shots, num_qubits = self.measurements().shape
            self._cached_metadata = {
                "num_shots": num_shots,
                "num_qubits": num_qubits,
                "execution_duration": self._execution_duration,
                "measurements": self.measurements(),
                "measurement_counts": self.measurement_counts(),
                "measurement_probabilities": self.measurement_probabilities(),
            }

        return self._cached_metadata

    def __repr__(self) -> str:
        return f"Result({self.metadata()})"

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
Module defining abstract GateModelJobResult Class

"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

import numpy as np


def normalize_batch_bit_lengths(measurements: list[dict[str, int]]) -> list[dict[str, int]]:
    """
    Normalizes the bit lengths of binary keys in measurement count dictionaries
    to ensure uniformity across all keys.

    Args:
        measurements (list[dict[str, int]]): A list of dictionaries where each dictionary
            contains binary string keys and integer values.

    Returns:
        list[dict[str, int]]: A new list of dictionaries with uniformly lengthened binary keys.
    """
    if len(measurements) == 0:
        return measurements

    max_bit_length = max(len(key) for counts in measurements for key in counts.keys())

    normalized_counts_list = []
    for counts in measurements:
        normalized_counts = {}
        for key, value in counts.items():
            normalized_key = key.zfill(max_bit_length)
            normalized_counts[normalized_key] = value
        normalized_counts_list.append(normalized_counts)

    return normalized_counts_list


def normalize_bit_lengths(measurement: dict[str, int]) -> dict[str, int]:
    """
    Normalizes the bit lengths of binary keys in a single measurement count dictionary
        to ensure uniformity across all keys.

    Args:
        measurement (dict[str, int]): A dictionary with binary string keys and integer values.

    Returns:
        dict[str, int]: A dictionary with uniformly lengthened binary keys.
    """
    normalized_list = normalize_batch_bit_lengths([measurement])

    return normalized_list[0] if normalized_list else measurement


class QuantumJobResult:
    """Result of a quantum job.

    Args:
        result (optional, Any): Result data

    """

    def __init__(self, result: Optional[Any] = None):
        self._result = result


class GateModelJobResult(ABC, QuantumJobResult):
    """Abstract interface for gate model quantum job results."""

    def measurements(self) -> Optional[np.ndarray]:
        """
        Return measurements as a 2d array where each row is a
        shot and each column is qubit. Defaults to None.

        """
        return None

    @abstractmethod
    def get_counts(self) -> Union[dict[str, int], list[dict[str, int]]]:
        """Returns histogram data of the run"""

    @staticmethod
    def counts_to_measurements(counts: dict[str, Any]) -> np.ndarray:
        """Convert counts dictionary to measurements array."""
        measurements = []
        for state, count in counts.items():
            measurements.extend([list(map(int, state))] * count)
        return np.array(measurements, dtype=int)

    @staticmethod
    def format_counts(counts: dict[str, int], include_zero_values: bool = False) -> dict[str, int]:
        """Formats, sorts, and adds missing bit indices to counts dictionary
        Can pass in a 'include_zero_values' parameter to decide whether to include the states
        with zero counts.

        For example:

        .. code-block:: python

            >>> counts
            {'1 1': 13, '0 0': 46, '1 0': 79}
            >>> GateModelJobResult.format_counts(counts)
            {'00': 46, '10': 79, '11': 13}
            >>> GateModelJobResult.format_counts(counts, include_zero_values=True)
            {'00': 46, '01': 0, '10': 79, '11': 13}

        """
        counts = {key.replace(" ", ""): value for key, value in counts.items()}

        num_bits = max(len(key) for key in counts)
        all_keys = [format(i, f"0{num_bits}b") for i in range(2**num_bits)]
        final_counts = {key: counts.get(key, 0) for key in sorted(all_keys)}

        if not include_zero_values:
            final_counts = {key: value for key, value in final_counts.items() if value != 0}

        return final_counts

    def measurement_counts(
        self, include_zero_values: bool = False
    ) -> Union[dict[str, int], list[dict[str, int]]]:
        """Returns the sorted histogram data of the run"""
        get_counts = self.get_counts()
        if isinstance(get_counts, dict):
            return self.format_counts(get_counts, include_zero_values=include_zero_values)

        batch_counts = [
            self.format_counts(counts, include_zero_values=include_zero_values)
            for counts in get_counts
        ]

        return normalize_batch_bit_lengths(batch_counts)

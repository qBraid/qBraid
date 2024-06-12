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
from typing import Any, Optional

import numpy as np


def normalize_measurement_counts(measurements: list[dict[str, int]]) -> list[dict[str, int]]:
    """
    Normalizes measurement count dictionaries to have the same bit length across all keys.

    Args:
        measurements (list[dict[str, int]]): A list of dicts with binary keys and integer values.

    Returns:
        list[dict[str, int]]: A new list of dictionaries with normalized key lengths.
    """
    if len(measurements) == 0:
        return measurements

    max_bit_length = max(len(key) for counts in measurements for key in counts.keys())

    normalized_counts_list = []
    for counts in measurements:
        normalized_counts = {}
        for key, true_value in counts.items():
            normalized_key = key.zfill(max_bit_length)
            normalized_counts[normalized_key] = true_value
        normalized_counts_list.append(normalized_counts)

    return normalized_counts_list


class QuantumJobResult:
    """Result of a quantum job.

    Args:
        result (optional, Any): Result data

    """

    def __init__(self, result: Optional[Any] = None):
        self._result = result


class GateModelJobResult(ABC, QuantumJobResult):
    """Abstract interface for gate model quantum job results."""

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

    def measurement_counts(self, include_zero_values: bool = False, **kwargs) -> dict:
        """Returns the sorted histogram data of the run"""
        raw_counts = self.raw_counts(**kwargs)
        if isinstance(raw_counts, dict):
            return self.format_counts(raw_counts, include_zero_values=include_zero_values)

        batch_counts = [
            self.format_counts(counts, include_zero_values=include_zero_values)
            for counts in raw_counts
        ]

        return normalize_measurement_counts(batch_counts)

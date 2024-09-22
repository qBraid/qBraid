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
Module for post-processing of raw results data.

"""
from __future__ import annotations

from typing import Any, Union


class GateModelResultBuilder:
    """Abstract interface for gate model quantum job results."""

    @staticmethod
    def format_counts(
        counts: dict[Any, Union[int, float]], include_zero_values: bool = False
    ) -> dict[Any, Union[int, float]]:
        """Formats, sorts, and adds missing bit indices to counts dictionary
        Can pass in a 'include_zero_values' parameter to decide whether to include the states
        with zero counts.

        For example:

        .. code-block:: python

            >>> counts
            {'1 1': 13, '0 0': 46, '1 0': 79}
            >>> GateModelResultBuilder.format_counts(counts)
            {'00': 46, '10': 79, '11': 13}
            >>> GateModelResultBuilder.format_counts(counts, include_zero_values=True)
            {'00': 46, '01': 0, '10': 79, '11': 13}

        """
        if all(isinstance(key, str) for key in counts.keys()):
            key_str_counts = {key.replace(" ", ""): value for key, value in counts.items()}

            num_bits = max(len(key) for key in key_str_counts)
            all_keys = [format(i, f"0{num_bits}b") for i in range(2**num_bits)]
            counts = {key: key_str_counts.get(key, 0) for key in sorted(all_keys)}

        if not include_zero_values:
            counts = {key: value for key, value in counts.items() if value != 0}

        return counts

    @staticmethod
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

    @staticmethod
    def normalize_bit_lengths(measurement: dict[str, int]) -> dict[str, int]:
        """
        Normalizes the bit lengths of binary keys in a single measurement count dictionary
            to ensure uniformity across all keys.

        Args:
            measurement (dict[str, int]): A dictionary with binary string keys and integer values.

        Returns:
            dict[str, int]: A dictionary with uniformly lengthened binary keys.
        """
        normalized_list = GateModelResultBuilder.normalize_batch_bit_lengths([measurement])

        return normalized_list[0] if normalized_list else measurement

    @staticmethod
    def normalize_counts(
        counts: Union[dict[str, int], list[dict[str, int]]], include_zero_values: bool = False
    ) -> Union[dict[str, int], list[dict[str, int]]]:
        """Returns the sorted histogram data of the run"""
        if isinstance(counts, dict):
            return GateModelResultBuilder.format_counts(
                counts, include_zero_values=include_zero_values
            )

        batch_counts = [
            GateModelResultBuilder.format_counts(counts, include_zero_values=include_zero_values)
            for counts in counts
        ]

        return GateModelResultBuilder.normalize_batch_bit_lengths(batch_counts)

    @staticmethod
    def _counts_to_probabilities(counts: dict[str, int]) -> dict[str, float]:
        """
        Convert histogram counts to probabilities.

        Args:
            counts (dict[str, int]): A dictionary with measurement outcomes as keys
                and their counts as values.

        Returns:
            dict[str, float]: A dictionary with measurement outcomes as keys and their
                probabilities as values.
        """
        total_counts = sum(counts.values())
        measurement_probabilities = {
            outcome: count / total_counts for outcome, count in counts.items()
        }
        return measurement_probabilities

    @staticmethod
    def counts_to_probabilities(
        counts: Union[dict[str, int], list[dict[str, int]]]
    ) -> Union[dict[str, float], list[dict[str, float]]]:
        """Calculate and return the probabilities of each measurement result."""
        counts = GateModelResultBuilder.normalize_counts(counts)
        if isinstance(counts, dict):
            return GateModelResultBuilder._counts_to_probabilities(counts)

        return [GateModelResultBuilder._counts_to_probabilities(count) for count in counts]

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
        counts: dict[Any, Union[int, float]],
        include_zero_values: bool = False,
        decimal: bool = False,
    ) -> dict[Any, Union[int, float]]:
        """
        Formats and sorts a counts dictionary with binary or integer keys.

        Args:
            counts (dict[Any, Union[int, float]]): Dictionary with keys as binary strings
                (e.g., '0 1') or integers (e.g., 3), and values as counts.
            include_zero_values (bool, optional): Include missing states with zero counts.
                Defaults to False.
            decimal (bool, optional): Convert binary keys to decimal integers. Defaults to False.

        Returns:
            dict[Any, Union[int, float]]: Sorted dictionary with formatted keys.

        Raises:
            ValueError: If keys are neither valid binary strings nor integers.

        Examples:
            Basic formatting with binary keys:
            >>> counts = {'1 1': 13, '0 0': 46, '1 0': 79}
            >>> format_counts(counts)
            {'00': 46, '10': 79, '11': 13}

            Include zero values:
            >>> format_counts(counts, include_zero_values=True)
            {'00': 46, '01': 0, '10': 79, '11': 13}

            Convert binary keys to decimal:
            >>> format_counts(counts, decimal=True)
            {0: 46, 1: 0, 2: 79, 3: 13}
        """
        input_is_dec = False
        input_is_bin = False

        if all(isinstance(key, str) for key in counts.keys()):
            if all(
                (key.startswith("0b") and set(key[2:]).issubset({"0", "1", " "}))
                or set(key).issubset({"0", "1", " "})
                for key in counts.keys()
            ):
                key_str_counts = {
                    (
                        key.replace(" ", "")[2:] if key.startswith("0b") else key.replace(" ", "")
                    ): value
                    for key, value in counts.items()
                }
                normalized_counts = GateModelResultBuilder.normalize_bit_lengths(key_str_counts)
                num_bits = max(len(key) for key in normalized_counts)
                all_keys = [format(i, f"0{num_bits}b") for i in range(2**num_bits)]
                counts = {key: normalized_counts.get(key, 0) for key in all_keys}
                input_is_bin = True
            elif all(key.isdigit() for key in counts.keys()):
                counts = {int(key): value for key, value in counts.items()}
                input_is_dec = True

        if decimal:
            if input_is_bin:
                counts = {int(key, 2): value for key, value in counts.items()}
            elif input_is_dec:
                counts = {int(key): value for key, value in counts.items()}

            if include_zero_values:
                max_key = max(counts)
                for i in range(max_key + 1):
                    if i not in counts:
                        counts[i] = 0

        elif input_is_dec or all(isinstance(key, int) for key in counts.keys()):
            counts = {bin(key): value for key, value in counts.items()}
            return GateModelResultBuilder.format_counts(
                counts, include_zero_values=include_zero_values, decimal=False
            )

        if not include_zero_values:
            counts = {key: value for key, value in counts.items() if value != 0}

        return dict(sorted(counts.items()))

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

        first_len = None
        all_keys_same_length = True
        max_bit_length = 0

        for counts in measurements:
            for key in counts.keys():
                key_len = len(key)
                if first_len is None:
                    first_len = key_len
                if key_len != first_len:
                    all_keys_same_length = False
                max_bit_length = max(max_bit_length, key_len)

        if all_keys_same_length:
            return measurements

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
        counts: Union[dict[str, int], list[dict[str, int]]],
        include_zero_values: bool = False,
        decimal: bool = False,
    ) -> Union[dict[str, int], list[dict[str, int]]]:
        """Returns the sorted histogram data of the run"""
        if isinstance(counts, dict):
            return GateModelResultBuilder.format_counts(
                counts, include_zero_values=include_zero_values, decimal=decimal
            )

        batch_counts = [
            GateModelResultBuilder.format_counts(
                counts, include_zero_values=include_zero_values, decimal=decimal
            )
            for counts in counts
        ]

        if decimal:
            return batch_counts

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
        counts: Union[dict[Any, int], list[dict[Any, int]]]
    ) -> Union[dict[Any, float], list[dict[Any, float]]]:
        """Calculate and return the probabilities of each measurement result."""
        if isinstance(counts, dict):
            return GateModelResultBuilder._counts_to_probabilities(counts)

        return [GateModelResultBuilder._counts_to_probabilities(count) for count in counts]

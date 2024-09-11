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
Module defining ExperimentalResult, ResultFormatter and RuntimeJobResult classes

"""
from dataclasses import dataclass
from typing import Any, Optional, Union

import numpy as np

from .enums import ExperimentType


@dataclass
class ExperimentalResult:
    """Class to represent the results of a quantum circuit experiment."""

    state_counts: dict
    measurements: Optional[np.ndarray]  # if gate_model_type it would be measurement counts
    # if AHS it would be the energy levels
    result_type: ExperimentType
    metadata: Optional[dict]
    execution_duration: float = -1.0

    def __repr__(self) -> str:
        return (
            f"ExperimentalResult(state_counts='{self.state_counts}', "
            f"measurements='{self.measurements}', result_type='{self.result_type}', "
            f"execution_duration={self.execution_duration})"
        )


class ResultFormatter:
    """Class to format and manipulate the results of a quantum circuit simulation."""

    @staticmethod
    def counts_to_measurements(counts: dict[str, Any]) -> np.ndarray:
        """Convert counts dictionary to measurements array."""
        measurements = []
        for state, count in counts.items():
            measurements.extend([list(map(int, state.strip()))] * count)
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
            >>> ResultFormatter.format_counts(counts)
            {'00': 46, '10': 79, '11': 13}
            >>> ResultFormatter.format_counts(counts, include_zero_values=True)
            {'00': 46, '01': 0, '10': 79, '11': 13}

        """
        if len(counts) == 0:
            return counts

        counts = {key.replace(" ", ""): value for key, value in counts.items()}

        num_bits = max(len(key) for key in counts)
        all_keys = [format(i, f"0{num_bits}b") for i in range(2**num_bits)]
        final_counts = {key: counts.get(key, 0) for key in sorted(all_keys)}

        if not include_zero_values:
            final_counts = {key: value for key, value in final_counts.items() if value != 0}

        return final_counts

    @staticmethod
    def counts_to_probabilities(counts: dict[str, int]) -> dict[str, float]:
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
    def array_to_histogram(arr: np.ndarray) -> dict[str, int]:
        """Convert a 2D numpy array to a histogram and cache the result."""
        row_strings = ["".join(map(str, row)) for row in arr]
        return {row: row_strings.count(row) for row in set(row_strings)}

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
        normalized_list = ResultFormatter.normalize_batch_bit_lengths([measurement])

        return normalized_list[0] if normalized_list else measurement

    @staticmethod
    def normalize_tuples(measurements: list[list[tuple[int, ...]]]) -> list[list[tuple[int, ...]]]:
        """
        Normalizes lists of tuples in a list to have the same tuple length across all entries
        by padding shorter tuples with zeros on the left.

        Args:
            measurements (list[list[tuple[int, ...]]]): A list of lists containing tuples
                with integer elements.

        Returns:
            list[list[tuple[int, ...]]]: A new list where each sublist's tuples have normalized
                lengths, preserving the binary significance of the numbers.
        """
        max_tuple_length = max(len(tup) for sublist in measurements for tup in sublist)

        normalized_measurements = []
        for sublist in measurements:
            normalized_sublist = []
            for tup in sublist:
                current_tuple = tuple(tup) if isinstance(tup, list) else tup
                padded_tuple = (0,) * (max_tuple_length - len(current_tuple)) + current_tuple
                normalized_sublist.append(padded_tuple)
            normalized_measurements.append(np.array(normalized_sublist))

        return np.array(normalized_measurements)

    @staticmethod
    def measurement_probabilities(counts) -> dict[str, float]:
        """Calculate and return the probabilities of each measurement result."""
        if isinstance(counts, dict):
            return ResultFormatter.counts_to_probabilities(counts)

        probabilities = [ResultFormatter.counts_to_probabilities(count) for count in counts]
        return probabilities


class RuntimeJobResult:
    """Class to store and retrieve the results of a quantum circuit simulation."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        job_id: str,
        device_id: str,
        results: list[ExperimentalResult],
        success: bool,
        errors=None,
    ):
        self.job_id = job_id
        self.device_id = device_id
        self.results = results
        self.success = success
        self.errors = errors
        self._cached_counts = {
            "decimal": None,
            "binary": None,
        }

    def __repr__(self) -> str:
        return (
            f"RuntimeJobResult(job_id='{self.job_id}', "
            f"device_id='{self.device_id}', num_experiments='{len(self.results)}', "
            f"success={self.success})"
        )

    def metadata(self, experiment_metadata=False):
        """Display the metadata of each experiment in the result"""

        for exp_num, experiment in enumerate(self.results):
            print(f"Experiment {exp_num} -")
            print(experiment)
            if experiment_metadata:
                print(experiment.metadata)

    def get_experiment(self, exp_num):
        """Return the experiment result for a specific experiment number"""
        if exp_num >= len(self.results):
            raise ValueError("Experiment number is greater than the number of experiments")
        return self.results[exp_num]

    def measurements(self) -> Union[np.ndarray, list[np.ndarray]]:
        """Get the list of measurements from the job result."""
        measurements = [experiment.measurements for experiment in self.results]
        if len(measurements) == 1:
            return measurements[0]
        return measurements

    def measurement_counts(
        self, include_zero_values: bool = False, decimal: bool = False
    ) -> Union[dict[str, int], list[dict[str, int]]]:
        """Returns the sorted histogram data of the run"""
        count_type = "decimal" if decimal else "binary"

        if self._cached_counts[count_type] is not None:
            return self._cached_counts[count_type]

        get_counts = [experiment.state_counts for experiment in self.results]

        if len(get_counts) == 0:
            raise ValueError("No measurements available")
        batch_counts = [
            (
                ResultFormatter.format_counts(counts, include_zero_values=include_zero_values)
                if experiment.result_type == ExperimentType.GATE_MODEL
                else counts
            )
            for counts, experiment in zip(get_counts, self.results)
        ]
        if decimal:
            decimal_counts = [
                {int(key, 2): value for key, value in counts.items()} for counts in batch_counts
            ]
            self._cached_counts["decimal"] = (
                decimal_counts[0] if len(decimal_counts) == 1 else decimal_counts
            )

            return self._cached_counts["decimal"]

        if len(batch_counts) == 1:
            self._cached_counts["binary"] = batch_counts[0]
            return batch_counts[0]

        self._cached_counts["binary"] = ResultFormatter.normalize_batch_bit_lengths(batch_counts)
        return self._cached_counts["binary"]

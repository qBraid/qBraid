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
Module defining qir-runner sparse quantum state simulator result class.

"""
from collections import defaultdict
from typing import Dict, List, Optional

import numpy as np


class Result:
    """Class to represent the results of a quantum circuit simulation."""

    def __init__(self, stdout: str, execution_duration: Optional[int] = None):
        self._raw_output = stdout
        self._parsed_data = self._parse_results(stdout)
        self._measurements = self._data_to_measurements()
        self._execution_duration = execution_duration
        self._cached_histogram = None
        self._cached_metadata = None

    @property
    def measurements(self) -> np.ndarray:
        """Return the measurement results as a 2D numpy array."""
        return self._measurements

    def measurement_counts(self, decimal: bool = False) -> Dict[str, int]:
        """Dynamically calculates and returns the histogram of measurement results."""
        counts = self._array_to_histogram(self.measurements)

        if decimal is True:
            counts = {int(key, 2): value for key, value in counts.items()}

        return counts

    def measurement_probabilities(self, **kwargs) -> Dict[str, float]:
        """Calculate and return the probabilities of each measurement result."""
        counts = self.measurement_counts(**kwargs)
        probabilities = self.counts_to_probabilities(counts)
        return probabilities

    def _parse_results(self, output: str) -> Dict[str, List[int]]:
        """Parse the raw output from the execution to extract measurement results."""
        results = defaultdict(list)
        current_shot_results = []

        for line in output.splitlines():
            elements = line.split()
            if len(elements) == 3 and elements[:2] == ["OUTPUT", "RESULT"]:
                _, _, bit = elements
                current_shot_results.append(int(bit))
            elif line.startswith("END"):
                for idx, result in enumerate(current_shot_results):
                    results[f"q{idx}"].append(result)
                current_shot_results = []

        return dict(results)

    def _data_to_measurements(self) -> np.ndarray:
        """Convert parsed data to a 2D array of measurement results."""
        if not self._parsed_data:
            return np.array([], dtype=np.int8)
        return np.array(
            [self._parsed_data[key] for key in sorted(self._parsed_data.keys())], dtype=np.int8
        ).T

    def _array_to_histogram(self, arr: np.ndarray) -> Dict[str, int]:
        """Implement caching mechanism here."""
        if self._cached_histogram is None:
            row_strings = ["".join(map(str, row)) for row in arr]
            self._cached_histogram = {row: row_strings.count(row) for row in set(row_strings)}
        return self._cached_histogram

    @staticmethod
    def counts_to_probabilities(counts: Dict[str, int]) -> Dict[str, float]:
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

    def metadata(self) -> Dict[str, int]:
        """Return metadata about the measurement results."""
        if self._cached_metadata is None:
            num_shots, num_qubits = self.measurements.shape
            self._cached_metadata = {
                "num_shots": num_shots,
                "num_qubits": num_qubits,
                "execution_duration": self._execution_duration,
                "measurements": self.measurements,
                "measurement_counts": self.measurement_counts(),
                "measurement_probabilities": self.measurement_probabilities(),
            }

        return self._cached_metadata

    def __repr__(self) -> str:
        return f"Result({self.metadata()})"

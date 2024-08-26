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
Module defining QbraidResult class

"""
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from qbraid.runtime.result import GateModelJobResult


@dataclass
class ExperimentResult:
    """Class to represent the results of a quantum circuit simulation."""

    measurement_counts: dict = field(default_factory=lambda: {})
    execution_duration: int = -1
    process_id: str = ""

    @staticmethod
    def from_result(result: dict[str, Any]):
        """Factory method to create JobResult from a result dictionary."""
        measurement_counts = result.get("measurementCounts", {})
        time_stamps: dict[str, Any] = result.get("timeStamps", {})
        execution_duration: int = time_stamps.get("executionDuration", -1)
        process_id: str = result.get("vendorJobId", "")

        return ExperimentResult(
            measurement_counts=measurement_counts,
            execution_duration=execution_duration,
            process_id=process_id,
        )


class QbraidJobResult(GateModelJobResult):
    """Class to represent the results of a quantum circuit simulation."""

    def __init__(self, device_id: str, job_id: str, success: bool, result: ExperimentResult):
        """Create a new Result object."""
        super().__init__()
        self.device_id = device_id
        self.job_id = job_id
        self.success = success
        self.result = result
        self._cached_histogram = None
        self._cached_metadata = None
        self._measurements = None

    def __repr__(self):
        """Return a string representation of the Result object."""
        return (
            f"QbraidJobResult(device_id='{self.device_id}', job_id='{self.job_id}', "
            f"success={self.success})"
        )

    def measurements(self):
        """Return the measurement results 2D numpy array."""
        if self._measurements is None:
            counts = self.result.measurement_counts
            if counts:
                self._measurements = self.counts_to_measurements(counts)
        return self._measurements

    def get_counts(self, decimal: bool = False):
        """Returns raw histogram data of the run"""
        measurements = self.measurements()
        if measurements is None:
            raise ValueError("No measurement data available.")

        counts = self._array_to_histogram(measurements)

        if decimal is True:
            counts = {int(key, 2): value for key, value in counts.items()}

        return counts

    def measurement_probabilities(self, **kwargs) -> dict[str, float]:
        """Calculate and return the probabilities of each measurement result."""
        counts = self.measurement_counts(**kwargs)
        probabilities = self.counts_to_probabilities(counts)
        return probabilities

    def _array_to_histogram(self, arr: np.ndarray) -> dict[str, int]:
        """Convert a 2D numpy array to a histogram and cache the result."""
        if self._cached_histogram is None:
            row_strings = ["".join(map(str, row)) for row in arr]
            self._cached_histogram = {row: row_strings.count(row) for row in set(row_strings)}
        return self._cached_histogram

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

    def metadata(self) -> dict[str, int]:
        """Return metadata about the measurement results."""
        if self._cached_metadata is None:
            num_shots, num_qubits = self.measurements().shape
            self._cached_metadata = {
                "num_shots": num_shots,
                "num_qubits": num_qubits,
                "execution_duration": self.result.execution_duration,
                "measurements": self.measurements(),
                "measurement_counts": self.measurement_counts(),
                "measurement_probabilities": self.measurement_probabilities(),
            }

        return self._cached_metadata

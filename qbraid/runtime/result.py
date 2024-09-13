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
Module defining abstract GateModelResultBuilder Class

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pprint import pformat
from typing import Any, Optional, Union

import numpy as np

from .enums import ExperimentType


class RuntimeResultBuilder(ABC):
    """Abstract interface for runtime quantum job results."""

    @property
    @abstractmethod
    def experiment_type(self) -> ExperimentType:
        """Returns the type of experiment"""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Returns a dictionary representation of the result"""


class GateModelResultBuilder(RuntimeResultBuilder, ABC):
    """Abstract interface for gate model quantum job results."""

    @property
    def experiment_type(self) -> ExperimentType:
        """Returns the type of experiment"""
        return ExperimentType.GATE_MODEL

    def measurements(self) -> Optional[Union[np.ndarray, list[np.ndarray]]]:
        """
        Return measurements as a 2d array where each row is a
        shot and each column is qubit. Defaults to None.

        """
        return None

    @abstractmethod
    def get_counts(self) -> Union[dict[str, int], list[dict[str, int]]]:
        """Returns histogram data of the run"""

    @staticmethod
    def measurements_to_counts(measurements: np.ndarray) -> dict[str, int]:
        """Convert a 2D numpy array to histogram counts data."""
        row_strings = ["".join(map(str, row)) for row in measurements]
        return {row: row_strings.count(row) for row in set(row_strings)}

    @staticmethod
    def format_counts(counts: dict[str, int], include_zero_values: bool = False) -> dict[str, int]:
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
        counts = {key.replace(" ", ""): value for key, value in counts.items()}

        num_bits = max(len(key) for key in counts)
        all_keys = [format(i, f"0{num_bits}b") for i in range(2**num_bits)]
        final_counts = {key: counts.get(key, 0) for key in sorted(all_keys)}

        if not include_zero_values:
            final_counts = {key: value for key, value in final_counts.items() if value != 0}

        return final_counts

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
        counts: Union[dict[str, float], list[dict[str, float]]]
    ) -> Union[dict[str, float], list[dict[str, float]]]:
        """Calculate and return the probabilities of each measurement result."""
        counts = GateModelResultBuilder.normalize_counts(counts)
        if isinstance(counts, dict):
            return GateModelResultBuilder._counts_to_probabilities(counts)

        return [GateModelResultBuilder._counts_to_probabilities(count) for count in counts]

    def to_dict(self) -> dict[str, Any]:
        """Returns a dictionary representation of the result"""
        raw_counts = self.get_counts()
        counts = self.normalize_counts(raw_counts)
        return {
            "shots": sum(counts.values()),
            "measured_qubits": len(next(iter(counts))),
            "measurement_counts": counts,
            "measurement_probabilities": self.counts_to_probabilities(counts),
            "measurements": self.measurements(),
        }


class GateModelResult:
    """Class for storing the result data of a quantum experiment."""

    def __init__(
        self,
        counts: Optional[Union[dict[str, int], list[dict[str, int]]]] = None,
        measurements: Optional[Union[np.ndarray, list[np.ndarray]]] = None,
    ):
        """Create a new GateModelResult instance."""
        self._counts = counts
        self._measurements = measurements
        self._cache = {
            "bin_nz": None,
            "bin_wz": None,
            "dec_nz": None,
            "dec_wz": None,
            "prob_bin_nz": None,
            "prob_bin_wz": None,
            "prob_dec_nz": None,
            "prob_dec_wz": None,
        }

    @classmethod
    def from_object(cls, result_builder: GateModelResultBuilder) -> GateModelResult:
        """Creates a new GateModelResult instance from a RuntimeResultBuilder instance."""
        result_data = result_builder.to_dict()
        return cls.from_dict(result_data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GateModelResult:
        """Creates a new GateModelResult instance from a dictionary."""
        counts = data.get("measurement_counts")
        measurements = data.get("measurements")
        return cls(counts=counts, measurements=measurements)

    @property
    def measurements(self) -> Optional[Union[np.ndarray, list[np.ndarray]]]:
        """Returns the measurements data of the run."""
        return self._measurements

    def get_counts(
        self, include_zero_values: bool = False, decimal: bool = False
    ) -> Union[dict[str, int], list[dict[str, int]]]:
        """
        Returns the histogram data of the run with optional zero values and binary/decimal keys.

        Args:
            include_zero_values (bool): Whether to include states with zero counts.
            decimal (bool): Whether to return counts with decimal keys (instead of binary).

        Returns:
            Union[dict[str, int], list[dict[str, int]]]: The histogram data.

        Raises:
            ValueError: If counts data is not available.
        """
        if self._counts is None:
            raise ValueError("Counts data is not available.")

        cache_key = f"{'dec' if decimal else 'bin'}_{'wz' if include_zero_values else 'nz'}"

        if self._cache[cache_key] is not None:
            return self._cache[cache_key]

        counts = GateModelResultBuilder.normalize_counts(
            self._counts, include_zero_values=include_zero_values
        )

        if decimal:
            counts = {int(k, 2): v for k, v in counts.items()}

        self._cache[cache_key] = counts

        return counts

    def get_probabilities(
        self, include_zero_values: bool = False, decimal: bool = False
    ) -> Union[dict[str, float], list[dict[str, float]]]:
        """
        Returns the probabilities of the measurement outcomes based on counts.

        Args:
            include_zero_values (bool): Whether to include states with zero probabilities.
            decimal (bool): Whether to return probabilities with decimal keys (instead of binary).

        Returns:
            Union[dict[str, float], list[dict[str, float]]]: The probabilities of the measurement outcomes.

        Raises:
            ValueError: If probabilities data is not available.
        """
        cache_key = f"prob_{'dec' if decimal else 'bin'}_{'wz' if include_zero_values else 'nz'}"

        if self._cache[cache_key] is not None:
            return self._cache[cache_key]

        counts = self.get_counts(include_zero_values=include_zero_values, decimal=decimal)
        probabilities = GateModelResultBuilder.counts_to_probabilities(counts)

        self._cache[cache_key] = probabilities

        return probabilities

    def __repr__(self) -> str:
        return f"GateModelResult(counts={self._counts})"


class Result:
    """Represents the results of a quantum job. This class is intended
    to be initialized by a QuantumJob class.

    Args:
        device_id (str): The ID of the device that executed the job.
        job_id (str): The ID of the job.
        success (bool): Whether the job was successful.
        result (ExperimentResult): The result of the job.
        metadata (dict[str, Any], optional): Additional metadata about the job results

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: str,
        job_id: str,
        success: bool,
        result: GateModelResult,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Create a new Result object."""
        self.device_id = device_id
        self.job_id = job_id
        self.success = success
        self.result = result
        self._metadata = metadata or {}

    def __repr__(self):
        """Return a string representation of the Result object."""
        return (
            f"Result(\n"
            f"  device_id={self.device_id},\n"
            f"  job_id={self.job_id},\n"
            f"  success={self.success},\n"
            f"  result={self.result},\n"
            f"  metadata={pformat(self._metadata, indent=4)}\n"
            f")"
        )

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

    def normalized_counts(
        self, include_zero_values: bool = False
    ) -> Union[dict[str, int], list[dict[str, int]]]:
        """Returns the sorted histogram data of the run"""
        res_counts = self.get_counts()
        if isinstance(res_counts, dict):
            return self.format_counts(res_counts, include_zero_values=include_zero_values)

        batch_counts = [
            self.format_counts(counts, include_zero_values=include_zero_values)
            for counts in res_counts
        ]

        return self.normalize_batch_bit_lengths(batch_counts)

    def measurement_probabilities(
        self, **kwargs
    ) -> Union[dict[str, float], list[dict[str, float]]]:
        """Calculate and return the probabilities of each measurement result."""
        counts = self.normalized_counts(**kwargs)
        if isinstance(counts, dict):
            return self.counts_to_probabilities(counts)

        return [self.counts_to_probabilities(count) for count in counts]

    def to_dict(self) -> dict[str, Any]:
        """Returns a dictionary representation of the result"""
        counts = self.normalized_counts()
        return {
            "shots": sum(counts.values()),
            "measured_qubits": len(next(iter(counts))),
            "measurement_counts": counts,
            "measurement_probabilities": self.measurement_probabilities(),
            "measurements": self.measurements(),
        }


@dataclass(frozen=True)
class ExperimentResult:
    """A dataclass for storing the result data of a quantum experiment.

    Attributes:
        experiment_type (ExperimentType): The quantum experiment type (e.g., gate-based, AHS).
        result_data (dict): Dictionary containing the results of the experiment (e.g. measurements).
    """

    experiment_type: ExperimentType
    result_data: dict

    @classmethod
    def from_object(cls, result_builder: RuntimeResultBuilder) -> ExperimentResult:
        """
        Creates a new ExperimentResult instance from a RuntimeResultBuilder instance.

        Args:
            result_builder (RuntimeResultBuilder): The runtime result object to extract data from.

        Returns:
            ExperimentResult: A new ExperimentResult instance.
        """
        return cls(
            experiment_type=result_builder.experiment_type, result_data=result_builder.to_dict()
        )

    def __repr__(self) -> str:
        return (
            f"ExperimentResult(\n"
            f"  experiment_type={self.experiment_type},\n"
            f"  result_data={pformat(self.result_data, indent=4)}\n"
            f")"
        )


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
        result: ExperimentResult,
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

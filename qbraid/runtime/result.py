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
Module containing models for schema-conformant Results.

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Union

import numpy as np

from .enums import ExperimentType
from .postprocess import GateModelResultBuilder
from .schemas import GateModelExperimentMetadata


class ResultData(ABC):
    """Abstract base class for runtime results linked to a
    specific :class:`~qbraid.runtime.ExperimentType`.
    """

    @property
    @abstractmethod
    def experiment_type(self) -> ExperimentType:
        """Returns the experiment type."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Converts the result data to a dictionary."""


class GateModelResultData(ResultData):
    """Class for storing and accessing the results of a gate model quantum job."""

    def __init__(
        self,
        measurement_counts: Optional[Union[dict[str, int], list[dict[str, int]]]] = None,
        measurements: Optional[Union[np.ndarray, list[np.ndarray]]] = None,
        **kwargs,
    ):
        """Create a new GateModelResult instance."""
        self._measurement_counts = measurement_counts
        self._measurements = measurements
        self._unscoped_data = kwargs
        self._cache = {
            "bin_nz": None,
            "bin_wz": None,
            "dec_nz": None,
            "dec_wz": None,
            "prob_bin_nz": None,
            "prob_bin_wz": None,
            "prob_dec_nz": None,
            "prob_dec_wz": None,
            "to_dict": None,
        }

    @property
    def experiment_type(self) -> ExperimentType:
        """Returns the experiment type."""
        return ExperimentType.GATE_MODEL

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GateModelResultData:
        """Creates a new GateModelResult instance from a dictionary."""
        measurement_counts = data.pop("measurement_counts", data.pop("measurementCounts", None))
        measurements = data.pop("measurements", None)

        if isinstance(measurements, list):
            measurements = np.array(measurements, dtype=object)

        return cls(measurement_counts=measurement_counts, measurements=measurements, **data)

    @classmethod
    def from_object(cls, model: GateModelExperimentMetadata, **kwargs) -> GateModelResultData:
        """Creates a new GateModelResultData instance from a GateModelExperimentMetadata object."""
        return cls.from_dict(model.model_dump(**kwargs))

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
        if self._measurement_counts is None:
            raise ValueError("Counts data is not available.")

        cache_key = f"{'dec' if decimal else 'bin'}_{'wz' if include_zero_values else 'nz'}"

        if self._cache[cache_key] is not None:
            return self._cache[cache_key]

        counts = GateModelResultBuilder.normalize_counts(
            self._measurement_counts, include_zero_values=include_zero_values
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
            Union[dict[str, float], list[dict[str, float]]]: Probabilities of measurement outcomes.

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

    def to_dict(self) -> dict[str, Any]:
        """Converts the GateModelResulData instance to a dictionary."""
        if self._cache["to_dict"] is not None:
            return self._cache["to_dict"]

        counts = self.get_counts()
        probabilities = self.get_probabilities()
        shots = sum(counts.values())
        num_measured_qubits = len(next(iter(counts)))
        data = {
            "shots": shots,
            "numMeasuredQubits": num_measured_qubits,
            "measurementCounts": counts,
            "measurementProbabilities": probabilities,
            "measurements": self._measurements,
        }
        self._cache["to_dict"] = data

        return data

    @staticmethod
    def _format_array(arr: np.ndarray) -> str:
        return f"array(shape={arr.shape}, dtype={arr.dtype})"

    def __repr__(self) -> str:
        if isinstance(self._measurements, np.ndarray):
            measurements_info = self._format_array(self._measurements)
        elif isinstance(self._measurements, list) and all(
            isinstance(arr, np.ndarray) for arr in self._measurements
        ):
            measurements_info = (
                "[" + ", ".join(self._format_array(arr) for arr in self._measurements) + "]"
            )
        else:
            measurements_info = self._measurements

        return (
            f"GateModelResultData(\n"
            f"  measurement_counts={self._measurement_counts},\n"
            f"  measurements={measurements_info}\n"
            f")"
        )


class Result:
    """Represents the results of a quantum job. This class is intended
    to be initialized by a QuantumJob class.

    Args:
        device_id (str): The ID of the device that executed the job.
        job_id (str): The ID of the job.
        success (bool): Whether the job was successful.
        data (ResultData): The result of the job.
        **details: Additional metadata about the job results

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: str,
        job_id: str,
        success: bool,
        data: ResultData,
        **kwargs,
    ):
        """Create a new Result object."""
        self.device_id = device_id
        self.job_id = job_id
        self.success = success
        self._data = data
        self._details = kwargs or {}

    @property
    def data(self) -> ResultData:
        """Returns the result of the job."""
        return self._data

    @property
    def details(self) -> dict[str, Any]:
        """Returns the result of the job."""
        return self._details

    def __repr__(self):
        """Return a string representation of the Result object."""
        out = (
            f"Result(\n"
            f"  device_id={self.device_id},\n"
            f"  job_id={self.job_id},\n"
            f"  success={self.success},\n"
            f"  data={self.data}"
        )
        if self.details:
            for key, value in self.details.items():
                if isinstance(value, str):
                    value_str = f"'{value}'"
                else:
                    value_str = repr(value)
                out += f",\n  {key}={value_str}"
        out += "\n)"
        return out

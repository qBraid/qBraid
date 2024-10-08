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

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, TypeVar, Union

import numpy as np
from qbraid_core import deprecated
from qbraid_core.system.generic import _datetime_to_str

from qbraid.programs import ExperimentType

from .postprocess import counts_to_probabilities, normalize_counts
from .schemas.experiment import AnnealingExperimentMetadata, GateModelExperimentMetadata

KeyType = TypeVar("KeyType", str, int)

MeasCount = dict[KeyType, int]

MeasProb = dict[KeyType, float]


class ResultData(ABC):
    """Abstract base class for runtime results linked to a
    specific :class:`~qbraid.programs.ExperimentType`.
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
        measurement_counts: Optional[Union[MeasCount, list[MeasCount]]] = None,
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

    @property
    def measurement_counts(self) -> Optional[Union[MeasCount, list[MeasCount]]]:
        """Returns the histogram data of the run as passed in the constructor."""
        return self._measurement_counts

    def get_counts(
        self, include_zero_values: bool = False, decimal: bool = False
    ) -> Union[MeasCount, list[MeasCount]]:
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

        counts = normalize_counts(
            self._measurement_counts, include_zero_values=include_zero_values, decimal=decimal
        )

        self._cache[cache_key] = counts

        return counts

    def get_probabilities(
        self, include_zero_values: bool = False, decimal: bool = False
    ) -> Union[MeasProb, list[MeasProb]]:
        """
        Returns the probabilities of the measurement outcomes based on counts.

        Args:
            include_zero_values (bool): Whether to include states with zero probabilities.
            decimal (bool): Whether to return probabilities with decimal keys (instead of binary).

        Returns:
            Union[MeasProb, list[MeasProb]: Probabilities of measurement outcomes.

        Raises:
            ValueError: If probabilities data is not available.
        """
        cache_key = f"prob_{'dec' if decimal else 'bin'}_{'wz' if include_zero_values else 'nz'}"

        if self._cache[cache_key] is not None:
            return self._cache[cache_key]

        counts = self.get_counts(include_zero_values=include_zero_values, decimal=decimal)
        probabilities = counts_to_probabilities(counts)

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
            "num_measured_qubits": num_measured_qubits,
            "measurement_counts": counts,
            "measurement_probabilities": probabilities,
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
            f"{self.__class__.__name__}("
            f"measurement_counts={self._measurement_counts}, "
            f"measurements={measurements_info}"
            f")"
        )


@dataclass
class AhsShotResult:
    """Class for storing the results of a single shot in an analog Hamiltonian simulation job."""

    success: bool
    pre_sequence: Optional[np.ndarray] = None
    post_sequence: Optional[np.ndarray] = None

    @staticmethod
    def _sequences_equal(seq1: Optional[np.ndarray], seq2: Optional[np.ndarray]) -> bool:
        """Helper function to compare two sequences, handling None values."""
        return (seq1 is None and seq2 is None) or (
            seq1 is not None and seq2 is not None and np.array_equal(seq1, seq2)
        )

    def __eq__(self, other):
        if not isinstance(other, AhsShotResult):
            return False
        return (
            self.success == other.success
            and self._sequences_equal(self.pre_sequence, other.pre_sequence)
            and self._sequences_equal(self.post_sequence, other.post_sequence)
        )


class AhsResultData(ResultData):
    """Class for storing and accessing the results of an analog Hamiltonian simulation job."""

    def __init__(
        self,
        measurement_counts: Optional[dict[str, int]] = None,
        measurements: Optional[list[AhsShotResult]] = None,
    ):
        self._measurement_counts = measurement_counts
        self._measurements = measurements

    @property
    def experiment_type(self) -> ExperimentType:
        """Returns the experiment type."""
        return ExperimentType.AHS

    @property
    def measurements(self) -> Optional[list[AhsShotResult]]:
        """Returns the measurements data of the run."""
        return self._measurements

    def get_counts(self) -> Optional[dict[str, int]]:
        """Returns the histogram data of the run."""
        return self._measurement_counts

    def to_dict(self) -> dict[str, Any]:
        """Converts the AhsResultData instance to a dictionary."""
        return {
            "measurement_counts": self._measurement_counts,
            "measurements": self._measurements,
        }


class AnnealingResultData(ResultData):
    """Class for storing and accessing the results of an annealing job."""

    def __init__(
        self, solutions: Optional[list[dict[str, Any]]] = None, num_solutions: Optional[int] = None
    ):
        self._solutions = solutions
        self._num_solutions = num_solutions

    @property
    def experiment_type(self) -> ExperimentType:
        """Returns the experiment type."""
        return ExperimentType.ANNEALING

    @classmethod
    def from_dict(cls, data: dict[str, Any] = None) -> AnnealingResultData:
        """Creates a new AnnealingResultData instance from a dictionary."""
        return cls(
            solutions=data.get("solutions"),
            num_solutions=data.get("num_solutions", data.get("numSolutions")),
        )

    @classmethod
    def from_object(cls, model: AnnealingExperimentMetadata, **kwargs) -> AnnealingResultData:
        """Creates a new AnnealingResultData instance from a AnnealingExperimentMetadata object."""
        return cls.from_dict(model.model_dump(**kwargs))

    @property
    def solutions(self) -> Optional[list[dict[str, Any]]]:
        """Returns the solutions data of the run."""
        return self._solutions

    @property
    def num_solutions(self) -> Optional[int]:
        """Returns the number of solutions."""
        if self._num_solutions is None and self._solutions is not None:
            self._num_solutions = len(self._solutions)
        return self._num_solutions

    def to_dict(self) -> dict[str, Any]:
        """Converts the AnnealingResultData instance to a dictionary."""
        return {
            "solutions": self.solutions,
            "num_solutions": self.num_solutions,
        }


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

    @deprecated("Use 'Result.data.get_counts()' instead.")
    def measurement_counts(self, *args, **kwargs) -> Any:
        """Returns the measurement counts of the job."""
        return self.data.get_counts(*args, **kwargs)

    @deprecated("Use 'Result.data.measurements' instead.")
    def measurements(self) -> Any:
        """Returns the measurements of the job."""
        return self.data.measurements

    def _format_value(self, value: Any, depth: int = 0, max_depth: int = 2) -> str:
        """Helper function to format nested values with a depth limit."""
        if isinstance(value, str):
            return f"'{value}'"
        if isinstance(value, Enum):
            return f"{value.name}"
        if isinstance(value, datetime.datetime):
            return _datetime_to_str(value)
        if isinstance(value, dict):
            if depth >= max_depth:
                return "{...}"
            if "openQasm" in value and value["openQasm"] is not None:
                value["openQasm"] = "..."
            return (
                "{"
                + ", ".join(
                    f"{k}: {self._format_value(v, depth + 1, max_depth)}" for k, v in value.items()
                )
                + "}"
            )
        if isinstance(value, list):
            if depth >= max_depth:
                return "[...]"
            return (
                "["
                + ", ".join(self._format_value(item, depth + 1, max_depth) for item in value)
                + "]"
            )
        return repr(value)

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
                formatted_value = self._format_value(value)
                out += f",\n  {key}={formatted_value}"
        out += "\n)"
        return out

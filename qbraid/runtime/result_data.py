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
Module containing models for schema-conformant ResultData classes.

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Type, TypeVar, Union, overload

import numpy as np

from qbraid.programs import ExperimentType

from .postprocess import counts_to_probabilities, normalize_data
from .schemas.experiment import (
    AhsExperimentMetadata,
    AnnealingExperimentMetadata,
    ExperimentMetadata,
    GateModelExperimentMetadata,
)

ResultDataType = TypeVar("ResultDataType", bound="ResultData")

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

    @classmethod
    @abstractmethod
    def from_dict(cls: Type[ResultDataType], data: dict[str, Any]) -> ResultDataType:
        """Creates a new ResultData instance from a dictionary."""

    @classmethod
    @overload
    def from_object(cls, model: GateModelExperimentMetadata, **kwargs) -> GateModelResultData: ...

    @classmethod
    @overload
    def from_object(cls, model: AnnealingExperimentMetadata, **kwargs) -> AnnealingResultData: ...

    @classmethod
    @overload
    def from_object(cls, model: AhsExperimentMetadata, **kwargs) -> AhsResultData: ...

    @classmethod
    def from_object(
        cls: Type[ResultDataType], model: ExperimentMetadata, **kwargs
    ) -> ResultDataType:
        """Creates a new ResultData instance from an ExperimentMetadata object."""
        return cls.from_dict(model.model_dump(**kwargs))


class GateModelResultData(ResultData):
    """Class for storing and accessing the results of a gate model quantum job."""

    def __init__(
        self,
        measurement_counts: Optional[Union[MeasCount, list[MeasCount]]] = None,
        measurements: Optional[Union[np.ndarray, list[np.ndarray]]] = None,
        measurement_probabilities: Optional[Union[MeasProb, list[MeasProb]]] = None,
        **kwargs,
    ):
        """Create a new GateModelResult instance."""
        self._measurement_counts = measurement_counts
        self._measurements = measurements
        self._measurement_probabilities = measurement_probabilities
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
        measurement_probabilities = data.pop("measurement_probabilities", None)

        if isinstance(measurements, list):
            measurements = np.array(measurements, dtype=object)

        return cls(
            measurement_counts=measurement_counts,
            measurements=measurements,
            measurement_probabilities=measurement_probabilities,
            **data,
        )

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
        counts = normalize_data(
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
            ValueError: If probabilities data is not available or
                        if measurement_probabilities is not a dictionary.
        """
        cache_key = f"prob_{'dec' if decimal else 'bin'}_{'wz' if include_zero_values else 'nz'}"

        if self._cache[cache_key] is not None:
            return self._cache[cache_key]

        if self._measurement_probabilities is not None:
            if not isinstance(self._measurement_probabilities, dict):
                raise ValueError("'measurement_probabilities' must be a dictionary.")

            probabilities = normalize_data(
                self._measurement_probabilities,
                include_zero_values=include_zero_values,
                decimal=decimal,
            )
        else:
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
            f"measurements={measurements_info}, "
            f"measurement_probabilities={self._measurement_probabilities}"
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

    def to_dict(self) -> dict[str, Union[bool, Optional[int]]]:
        """Convert the instance to a dictionary, converting numpy arrays to lists."""
        return {
            "success": self.success,
            "pre_sequence": self.pre_sequence.tolist() if self.pre_sequence is not None else None,
            "post_sequence": (
                self.post_sequence.tolist() if self.post_sequence is not None else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Union[bool, Optional[list[int]]]]) -> AhsShotResult:
        """Create an instance from a dictionary, converting lists to numpy arrays."""
        return cls(
            success=data["success"],
            pre_sequence=(
                np.array(data["pre_sequence"]) if data.get("pre_sequence") is not None else None
            ),
            post_sequence=(
                np.array(data["post_sequence"]) if data.get("post_sequence") is not None else None
            ),
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AhsResultData:
        """Creates a new AhsResultData instance from a dictionary."""
        measurements = data.get("measurements")
        if measurements is not None:
            if not isinstance(measurements, list):
                raise ValueError("'measurements' must be a list or None.")
            if not all(isinstance(shot, dict) for shot in measurements):
                raise ValueError("Each item in 'measurements' must be a dictionary.")
            measurements = [AhsShotResult.from_dict(shot) for shot in measurements]

        return cls(
            measurements=measurements,
            measurement_counts=data.get("measurement_counts", data.get("measurementCounts")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Converts the AhsResultData instance to a dictionary."""
        return {
            "measurement_counts": self._measurement_counts,
            "measurements": self._measurements,
        }

    def __eq__(self, other):
        if not isinstance(other, AhsResultData):
            return False

        if self._measurement_counts != other._measurement_counts:
            return False

        if self._measurements is None and other._measurements is None:
            return True
        if self._measurements is None or other._measurements is None:
            return False
        if len(self._measurements) != len(other._measurements):
            return False

        return all(s1 == s2 for s1, s2 in zip(self._measurements, other._measurements))

    def __repr__(self) -> str:
        """Return a string representation of the AhsResultData instance."""
        return f"{self.__class__.__name__}(measurement_counts={self._measurement_counts}, measurements={self._measurements})"  # pylint: disable=line-too-long


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
    def from_dict(cls, data: dict[str, Any]) -> AnnealingResultData:
        """Creates a new AnnealingResultData instance from a dictionary."""
        return cls(
            solutions=data.get("solutions"),
            num_solutions=data.get("num_solutions", data.get("numSolutions")),
        )

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

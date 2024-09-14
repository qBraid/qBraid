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
from pprint import pformat
from typing import Any, Optional, Union

import numpy as np

from .enums import ExperimentType
from .postprocess import GateModelResultBuilder


class RuntimeResult:
    """Base class for runtime result types.

    .. note:: This class is primarily intended for type checking, but can be inherited
              from directly if the new result type doesn't align with existing abstract
              classes tied to specific :class:`~qbraid.runtime.ExperimentType`.
    """


class ExperimentResult(RuntimeResult, ABC):
    """Abstract base class for runtime results linked to a
    specific :class:`~qbraid.runtime.ExperimentType`.
    """

    @property
    @abstractmethod
    def experiment_type(self) -> ExperimentType:
        """Returns the experiment type."""


class GateModelResult(ExperimentResult):
    """Class for storing and accessing the results of a gate model quantum job."""

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

    @property
    def experiment_type(self) -> ExperimentType:
        """Returns the experiment type."""
        return ExperimentType.GATE_MODEL

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GateModelResult:
        """Creates a new GateModelResult instance from a dictionary."""
        counts = data.get("counts")
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

    def metadata(self) -> dict[str, int]:
        """Return metadata about the measurement results."""
        if self._cache["metadata"] is not None:
            return self._cache["metadata"]

        counts = self.get_counts()
        probabilities = self.get_probabilities()
        shots = sum(counts.values())
        num_qubits = len(next(iter(counts)))
        metadata = {
            "num_shots": shots,
            "num_qubits": num_qubits,
            "measurement_counts": counts,
            "measurement_probabilities": probabilities,
        }
        self._cache["metadata"] = metadata

        return metadata

    def to_dict(self) -> dict[str, Any]:
        """Converts the GateModelResult instance to a dictionary."""
        return {"counts": self._counts, "measurements": self._measurements}

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

        return f"GateModelResult(counts={self._counts}, measurements={measurements_info})"


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

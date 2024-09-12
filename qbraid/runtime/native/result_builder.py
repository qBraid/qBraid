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

from qbraid.runtime.result import GateModelResultBuilder


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


class QbraidGateModelResultBuilder(GateModelResultBuilder):
    """Class to represent the results of a quantum circuit simulation."""

    def __init__(self, device_id: str, job_id: str, success: bool, result: ExperimentResult):
        """Create a new result builder object."""
        self.device_id = device_id
        self.job_id = job_id
        self.success = success
        self.result = result
        self._cached_metadata = None

    def __repr__(self):
        """Return a string representation of the Result object."""
        return (
            f"QbraidGateModelResultBuilder(device_id='{self.device_id}', job_id='{self.job_id}', "
            f"success={self.success})"
        )

    def get_counts(self, decimal: bool = False):
        """Returns raw histogram data of the run"""
        counts = self.result.measurement_counts

        if decimal is True:
            counts = {int(key, 2): value for key, value in counts.items()}

        return counts

    def metadata(self) -> dict[str, int]:
        """Return metadata about the measurement results."""
        if self._cached_metadata is None:
            counts = self.normalized_counts()
            self._cached_metadata = {
                "num_shots": sum(counts.values()),
                "num_qubits": len(next(iter(counts))),
                "execution_duration": self.result.execution_duration,
                "measurement_counts": counts,
                "measurement_probabilities": self.measurement_probabilities(),
            }

        return self._cached_metadata

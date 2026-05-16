# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module containing models for schema-conformant Results.

"""
from __future__ import annotations

import copy
import datetime
from enum import Enum
from typing import Any, Generic

from qbraid_core import deprecated
from qbraid_core.system.generic import _datetime_to_str

from .result_data import GateModelResultData, ResultDataType


class Result(Generic[ResultDataType]):
    """Represents the results of a quantum job. This class is intended
    to be initialized by a QuantumJob class.

    Args:
        device_id (str): The ID of the device that executed the job.
        job_id (str or int): The ID of the job.
        success (bool): Whether the job was successful.
        data (ResultData): The result of the job.
        **details: Additional metadata about the job results

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: str,
        job_id: str | int,
        success: bool,
        data: ResultDataType,
        **kwargs,
    ):
        """Create a new Result object."""
        self.device_id = device_id
        self.job_id = job_id
        self.success = success
        self._data = data
        self._details = kwargs or {}

    @property
    def data(self) -> ResultDataType:
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

            data = copy.deepcopy(value)
            if "compiledOutput" in data and data["compiledOutput"] is not None:
                data["compiledOutput"] = "..."
            return (
                "{"
                + ", ".join(
                    f"{k}: {self._format_value(v, depth + 1, max_depth)}" for k, v in data.items()
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


class BatchResult(Generic[ResultDataType]):
    """Represents the results of a batch quantum job.

    Wraps a list of per-circuit :class:`Result` objects and provides
    aggregate access to measurement data and per-circuit metadata.

    Args:
        device_id: The ID of the device that executed the job.
        job_id: The ID of the job.
        success: Whether the job completed successfully.
        results: Per-circuit Result objects.
        **kwargs: Aggregate metadata (e.g. time_stamps, cost, status).
    """

    def __init__(
        self,
        device_id: str,
        job_id: str | int,
        success: bool,
        results: list[Result[ResultDataType]],
        **kwargs,
    ):
        self.device_id = device_id
        self.job_id = job_id
        self.success = success
        self._results = results
        self._aggregate_details = kwargs or {}
        self._data: ResultDataType | None = None

    @property
    def num_circuits(self) -> int:
        """Returns the number of circuits in the batch."""
        return len(self._results)

    @property
    def results(self) -> list[Result[ResultDataType]]:
        """Returns the per-circuit Result objects."""
        return self._results

    @property
    def data(self) -> ResultDataType:
        """Returns aggregated result data across all circuits.

        For gate model jobs, ``get_counts()`` and ``get_probabilities()``
        return lists indexed by circuit position.
        """
        if self._data is None:
            self._data = self._build_aggregate_data()
        return self._data

    @property
    def details(self) -> list[dict[str, Any]]:
        """Returns per-circuit metadata, indexed by circuit position."""
        return [r.details for r in self._results]

    def _build_aggregate_data(self) -> ResultDataType:
        """Collects per-circuit measurement data into a single ResultData."""
        counts = []
        probabilities = []
        has_counts = False
        has_probs = False

        for r in self._results:
            rd = r.data
            if isinstance(rd, GateModelResultData):
                if rd.measurement_counts is not None:
                    counts.append(rd.measurement_counts)
                    has_counts = True
                else:
                    counts.append({})

                if rd._measurement_probabilities is not None:
                    probabilities.append(rd._measurement_probabilities)
                    has_probs = True
                else:
                    probabilities.append({})

        return GateModelResultData(
            measurement_counts=counts if has_counts else None,
            measurement_probabilities=probabilities if has_probs else None,
        )

    def __repr__(self):
        """Return a string representation of the BatchResult object."""
        return (
            f"BatchResult(\n"
            f"  device_id={self.device_id},\n"
            f"  job_id={self.job_id},\n"
            f"  success={self.success},\n"
            f"  num_circuits={self.num_circuits}\n"
            f")"
        )

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

import copy
import datetime
from enum import Enum
from typing import Any, Generic

from qbraid_core import deprecated
from qbraid_core.system.generic import _datetime_to_str

from .result_data import ResultDataType


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
            if "openQasm" in data and data["openQasm"] is not None:
                data["openQasm"] = "..."
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

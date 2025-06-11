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
Module defining Rigetti job class

"""

import warnings
from typing import TYPE_CHECKING, Any, TypeVar

import pyquil.api
from qcs_sdk.qpu.api import QpuApiError

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    from .device import RigettiDevice

T = TypeVar("T")
"""A generic parameter describing the opaque job handle returned from QAM#execute and subclasses."""


class RigettiJobError(QbraidRuntimeError):
    """Class for errors raised while processing an Rigetti job."""


class RigettiJob(QuantumJob):
    """Rigetti job class."""

    def __init__(
        self,
        job_id: str | int,
        device: "RigettiDevice",
        execute_response: T,
        **kwargs: Any,
    ):
        """
        Initialize the Rigetti job with a job ID and an optional device.
        """
        super().__init__(job_id=job_id, **kwargs)
        self._qam = device._qc.qam
        self._execute_response = execute_response
        self._device = device
        self._status = JobStatus.RUNNING

    def status(self) -> JobStatus:
        """Return the current status of the Rigetti job."""
        return self._status

    def cancel(self) -> None:
        """Cancel the Rigetti job."""
        if isinstance(self._qam, pyquil.api.QPU):
            try:
                self._status = JobStatus.CANCELLING
                self._qam.cancel(self._execute_response)
            except Exception:  # pylint: disable=W0718
                warnings.warn(
                    UserWarning(
                        "Failed to cancel the QPU job. "
                        "Cancellation is not guaranteed, as it "
                        "is based on job state at the time of cancellation."
                    )
                )
                self._status = JobStatus.RUNNING
            else:
                self._status = JobStatus.CANCELLED
        warnings.warn(UserWarning("QVM jobs cannot be cancelled."))

    def get_result(self) -> dict[str, Any]:
        """
        Translate Rigetti's readout data into a format that
        can be consumed by qBraid runtime.

        """
        qam_execution_result = self._qam.get_result(self._execute_response)
        readout = qam_execution_result.get_register_map().get("ro")
        measurements = ["".join(map(str, row)) for row in readout]
        counts = {row: measurements.count(row) for row in set(measurements)}
        total_counts = sum(counts.values())
        probabilities = {outcome: count / total_counts for outcome, count in counts.items()}
        return {"counts": counts, "probabilities": probabilities}

    def result(self) -> Result:
        """Return the result of the Rigetti job."""
        try:
            result = self.get_result()  # blocks until the job is complete
        except QpuApiError:
            self._status = JobStatus.FAILED
            return Result(
                device_id=self._device.profile.device_id,
                job_id=self._job_id,
                success=False,
                data=None,
            )
        self._status = JobStatus.COMPLETED

        return Result(
            device_id=self._device.profile.device_id,
            job_id=self._job_id,
            success=True,
            data=GateModelResultData(
                measurement_counts=result["counts"],
                measurement_probabilities=result["probabilities"],
            ),
        )

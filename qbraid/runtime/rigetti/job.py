# Copyright (C) 2026 qBraid
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
from typing import TYPE_CHECKING, Any

from qcs_sdk.qpu.api import QpuApiError, cancel_job, retrieve_results

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    from .device import RigettiDevice


class RigettiJobError(QbraidRuntimeError):
    """Class for errors raised while processing an Rigetti job."""


class RigettiJob(QuantumJob):
    """Rigetti job class."""

    def __init__(
        self,
        job_id: str | int,
        device: "RigettiDevice",
        **kwargs: Any,
    ):
        super().__init__(job_id=job_id, **kwargs)
        self._device = device
        self._status = JobStatus.RUNNING

    @property
    def _quantum_processor_id(self) -> str:
        return self._device.profile.device_id

    @property
    def _client(self):
        return self._device._qcs_client

    def status(self) -> JobStatus:
        """Return the current status of the Rigetti job."""
        return self._status

    def cancel(self) -> None:
        """Cancel the Rigetti job."""
        try:
            self._status = JobStatus.CANCELLING
            cancel_job(
                job_id=self._job_id,
                quantum_processor_id=self._quantum_processor_id,
                client=self._client,
            )
        except QpuApiError:
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

    def get_result(self) -> dict[str, Any]:
        """
        Retrieve and translate Rigetti's readout data into a format
        that can be consumed by qBraid runtime.
        """
        execution_results = retrieve_results(
            job_id=self._job_id,
            quantum_processor_id=self._quantum_processor_id,
            client=self._client,
        )
        ro_data = execution_results.buffers.get("ro")
        if ro_data is None:
            raise RigettiJobError("No 'ro' readout buffer found in execution results.")

        readout = ro_data.data
        measurements = ["".join(map(str, map(int, row))) for row in readout]
        counts = {row: measurements.count(row) for row in set(measurements)}
        total_counts = sum(counts.values())
        probabilities = {outcome: count / total_counts for outcome, count in counts.items()}
        return {"counts": counts, "probabilities": probabilities}

    def result(self) -> Result:
        """Return the result of the Rigetti job."""
        try:
            result = self.get_result()
        except (QpuApiError, RigettiJobError) as e:
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
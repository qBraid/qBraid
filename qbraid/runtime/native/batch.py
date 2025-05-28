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
Module defining the QbraidBatchJob Class

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from qbraid._logging import logger
from qbraid.runtime.batch import BatchQuantumJob
from qbraid.runtime.enums import BatchJobStatus, JobStatus
from qbraid.runtime.exceptions import ResourceNotFoundError

if TYPE_CHECKING:
    import qbraid.runtime
    from qbraid.runtime.result_data import ResultDataType


class QbraidBatchJob(BatchQuantumJob):
    """Qbraid batch job class."""

    def __init__(
        self, device: qbraid.runtime.QuantumDevice, max_timeout: Optional[int] = None, **kwargs
    ):
        super().__init__(device, max_timeout, **kwargs)

    def status(self) -> BatchJobStatus:
        """Return the status of the batch, among the values of ``BatchJobStatus``."""

        if not self.id or not self.is_active():
            raise ResourceNotFoundError(
                "Batch is not active. Please activate batch before status can be retrieved."
            )
        # TODO: cache this status value for the batch
        statuses = set([job.status() for job in self.jobs])
        if self.is_active():
            # we have a unified status for the batch jobs
            if len(statuses) == 1:
                status = statuses.pop()  # Get the single status from the set
                status_mapping = {
                    JobStatus.RUNNING: BatchJobStatus.RUNNING,
                    JobStatus.COMPLETED: BatchJobStatus.COMPLETED,
                    JobStatus.QUEUED: BatchJobStatus.QUEUED,
                    JobStatus.CANCELLED: BatchJobStatus.CANCELLED,
                    JobStatus.FAILED: BatchJobStatus.FAILED,
                    JobStatus.INITIALIZING: BatchJobStatus.INITIALIZING,
                }
                return status_mapping[status]
            else:
                return BatchJobStatus.PARTIAL

    def result(self) -> list[qbraid.runtime.Result[ResultDataType]]:
        """Return the results of the batch."""
        if not self.is_active():
            raise ResourceNotFoundError(
                "Batch is not active. Please create batch before results can be retrieved."
            )
        if not self.jobs:
            raise ResourceNotFoundError(
                "No jobs found in the batch. Please add jobs before retrieving results."
            )
        return [job.result() for job in self.jobs]

    def cancel(self) -> None:
        """Attempt to cancel the batch."""
        if not self.is_active():
            raise ResourceNotFoundError(
                "Batch is not active. Please create batch before it can be cancelled."
            )
        if not self.jobs:
            raise ResourceNotFoundError(
                "No jobs found in the batch. Please add jobs before cancelling."
            )
        for job in self.jobs:
            try:
                job.cancel()
            except Exception as e:
                logger.error(f"Failed to cancel job {job.id}: {e}")
        logger.info("Batch cancelled successfully.")

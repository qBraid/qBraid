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

from qbraid_core.services.quantum import QuantumClient

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
        self, 
        device: qbraid.runtime.QuantumDevice, max_timeout: Optional[int] = None,
        client: Optional[qbraid_core.services.quantum.QuantumClient] = None,
        **kwargs
    ):
        super().__init__(device, max_timeout, **kwargs)
        self._client = client 

    @property
    def client(self) -> qbraid_core.services.quantum.QuantumClient:
        """
        Lazily initializes and returns the client object associated with the batch.
        If the batch has an associated device with a client, that client is used.
        Otherwise, a new instance of QuantumClient is created and used.

        Returns:
            QuantumClient: The client object associated with the batch.
        """
        if self._client is None:
            self._client = self._device.client if self._device else QuantumClient()
        return self._client

    def status(self) -> BatchJobStatus:
        """Return the status of the batch, among the values of ``BatchJobStatus``."""

        if not self.id or not self.is_active():
            raise ResourceNotFoundError(
                "Batch is not active. Please activate batch before status can be retrieved."
            )
        
        if self.is_terminal_state() and self._cache_metadata.get("status"):
            # if the batch is terminal, we can return the cached status
            return self._cache_metadata["status"]
        
        # get back the status from the API

        # TODO: implement refresh_batch in the client
        self._cache_metadata["status"] = self.client.refresh_batch(self.id)
        # TODO: implement refresh_batch in the client

        if self.is_active() and self._cache_metadata["status"] in JobStatus.terminal_states():
            # if the batch is active but the status is terminal, we update the status
            self._active = False
        
        return self._cache_metadata["status"]

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
        logger.info(f"Cancelling batch {self.id} with {len(self.jobs)} jobs.")

        # will implicitly cancel all jobs in the batch IN the API 

        # TODO: implement cancel_batch in the client
        self.client.cancel_batch(self.id)
        # TODO: implement cancel_batch in the client


        # DO WE TOUCH THE STATUS HERE? 
        logger.info("Batch cancelled successfully.")

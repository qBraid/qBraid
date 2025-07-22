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
Module defining abstract BatchQuantumJob Class

"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from time import sleep, time
from typing import TYPE_CHECKING, Any, Optional

from qbraid_core.services.quantum import QuantumClient

from qbraid._logging import logger

from .enums import BatchJobStatus
from .exceptions import BatchJobError, ResourceNotFoundError
from .job import QuantumJob

if TYPE_CHECKING:
    import qbraid.runtime
    from qbraid.runtime.result_data import ResultDataType


class BatchQuantumJob(ABC):
    """Abstract interface for batch-like classes."""

    MAX_TIMEOUT_DEFAULT = 60 * 60  # 1 hour
    MAX_TIMEOUT_LIMIT = 24 * 60 * 60  # 24 hours

    def __init__(
        self,
        device: qbraid.runtime.QuantumDevice,
        client: Optional[QuantumClient] = None,
        max_timeout: Optional[int] = None,
        **kwargs,
    ):
        self._device = device
        self._client = client
        self._jobs: list[QuantumJob] = []
        self.max_timeout = max_timeout if max_timeout is not None else self.MAX_TIMEOUT_DEFAULT
        self._cache_metadata = {**kwargs}
        self._active = False
        self._batch_id = device.create_batch(self.max_timeout)

    @property
    def id(self) -> str | int:  # pylint: disable=invalid-name
        """Return a unique id identifying the batch."""
        return self._batch_id

    @property
    def device(self) -> qbraid.runtime.QuantumDevice:
        """Returns the qbraid QuantumDevice object associated with this batch."""
        return self._device

    @property
    def client(self) -> QuantumClient:
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

    @property
    def jobs(self) -> list[QuantumJob]:
        """Return the locally cached list of jobs in the batch.
        To refresh this list from the backend, call `fetch_jobs()`."""
        return self._jobs

    @jobs.setter
    def jobs(self, jobs: list[QuantumJob]) -> None:
        """Set the list of jobs in the batch."""
        if not all(isinstance(job, QuantumJob) for job in jobs):
            raise TypeError("All jobs in the batch must be QuantumJob instances.")

    def _fetch_jobs_from_backend(self) -> list[dict]:
        """
        Fetches job information from the backend for the current batch.

        This method retrieves the batch job information from the client,
        extracts the list of jobs associated with the batch, and performs
        some basic logging.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary contains
                        information about a job in the batch. If no jobs are found,
                        an empty list is returned.

        Note:
            This method logs a warning if no jobs are found for the batch,
            and logs debug information about the number of jobs retrieved.
        """
        batch_job = self.client.get_batch_job(self.id)
        jobs = batch_job.get("jobs", [])
        if not jobs:
            logger.warning("No jobs found for batch ID: %s", self.id)
        logger.debug("Retrieved %d jobs for batch ID: %s", len(jobs), self.id)
        return jobs

    @abstractmethod
    def fetch_jobs(self) -> list[QuantumJob]:
        """Fetch the jobs associated with the batch from the backend and populate the
        `._jobs` attribute with instances of provider specific QuantumJob classes."""

    @property
    def max_timeout(self) -> int:
        """Return the maximum timeout for the batch."""
        return self._max_timeout

    @max_timeout.setter
    def max_timeout(self, value: int) -> None:
        """Set the maximum timeout for the batch."""
        if not isinstance(value, int):
            raise TypeError("Maximum timeout must be an integer.")

        if value <= 0:
            raise ValueError("Maximum timeout must be a positive integer.")

        if value > self.MAX_TIMEOUT_LIMIT:
            raise ValueError(
                f"Maximum timeout cannot exceed 24 hours ({self.MAX_TIMEOUT_LIMIT} seconds)."
            )

        self._max_timeout = value

    def begin(self):
        """Begin the batch job context."""
        if self.is_active():
            logger.warning("Batch '%s' is already active. No action taken on begin.", self.id)
            return
        try:
            # activate the batch on the device
            self.device.activate_batch(self.id)
            self._active = True
        except Exception as e:
            self._active = False
            raise BatchJobError(
                f"Failed to activate batch on device '{self.device.profile.device_id}'."
            ) from e

    def close(self):
        """Close the batch job context."""
        if not self.is_active():
            logger.warning("Batch '%s' is not active. No action taken on close.", self.id)
            return
        try:
            # deactivate the batch on the device
            self.device.close_batch(self.id)
            self._active = False

            # update the jobs cache
            self.fetch_jobs()
        except Exception as e:
            raise BatchJobError(
                f"Failed to close batch '{self.id}' on device '{self.device.profile.device_id}'."
            ) from e

    def __enter__(self) -> BatchQuantumJob:
        """Enter the runtime context of the batch job."""
        self.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context of the batch job."""
        if exc_type is not None:
            logger.error("An error occurred while processing batch '%s': %s", self.id, exc_value)

        self.close()
        return False

    def is_active(self) -> bool:
        """Returns True if the batch is active. False otherwise."""
        return self._active

    def is_terminal_state(self) -> bool:
        """Returns True if batch is in final state. False otherwise."""
        terminal_states = BatchJobStatus.terminal_states()
        if self._cache_metadata.get("status", None) in terminal_states:
            return True

        status = self.status()
        return status in terminal_states

    def metadata(self) -> dict[str, Any]:
        """Return the metadata regarding the batch."""
        status = self.status()
        self._cache_metadata["status"] = status
        return self._cache_metadata

    def wait_for_final_state(self, timeout: Optional[int] = None, poll_interval: int = 5) -> None:
        """Poll the batch status until all its jobs progress to a final state.

        Args:
            timeout: Seconds to wait for the batch. If ``None``, wait indefinitely.
            poll_interval: Seconds between queries. Defaults to 5 seconds.

        Raises:
            JobStateError: If the batch does not reach a final state before the specified timeout.

        """
        start_time = time()
        while not self.is_terminal_state():
            elapsed_time = time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise TimeoutError(f"Timeout while waiting for job {self.id}.")
            sleep(poll_interval)

    async def _wait_for_final_state(
        self, timeout: Optional[int] = None, poll_interval: int = 5
    ) -> None:
        """Asynchronously wait for the batch to reach a terminal state (e.g., COMPLETED, FAILED).

        This non-blocking method uses asyncio to periodically poll the batch's status,
        allowing other coroutines to run while waiting. It is especially useful in
        asynchronous applications where blocking the event loop is undesirable.

        Args:
            timeout (Optional[int]): Maximum number of seconds to wait for the batch.
                If None, waits indefinitely.
            poll_interval (int): Seconds between queries. Defaults to 5.

        Raises:
            TimeoutError: If the batch does not reach a terminal state before the specified timeout.
        """
        start_time = time()
        while not self.is_terminal_state():
            elapsed_time = time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise TimeoutError(f"Timeout while waiting for batch {self.id}.")
            await asyncio.sleep(poll_interval)

    async def async_result(
        self, timeout: Optional[int] = None, poll_interval: int = 5
    ) -> qbraid.runtime.Result[ResultDataType]:
        """Asynchronously wait for the job to reach a final state and return the result.

        This method provides a non-blocking way to poll the job status using asyncio.
        It allows developers to `await` the job without blocking the event loop,
        making it suitable for integration in async applications and pipelines.

        Args:
            timeout (Optional[int]): Maximum number of seconds to wait for the job.
                If None, waits indefinitely.
            poll_interval (int): Seconds between status checks. Defaults to 5.

        Returns:
            Result[ResultDataType]: The result object associated with the job,
            if successfully completed.

        Raises:
            TimeoutError: If the job does not reach a terminal state before the timeout expires.
        """
        await self._wait_for_final_state(timeout, poll_interval)
        return self.result()

    def result(self) -> list[qbraid.runtime.Result[ResultDataType]]:
        """Return the results of the batch. This is blocking method that waits for the results
        of all jobs in the batch to be available."""

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
        """Attempt to cancel the current jobs in the batch."""
        if not self.is_active():
            raise ResourceNotFoundError(
                "Batch is not active. Please create batch before it can be cancelled."
            )
        if not self.jobs:
            raise ResourceNotFoundError(
                "No jobs found in the batch. Please add jobs before cancelling."
            )
        logger.info("Cancelling batch '%s' with %d jobs.", self.id, len(self.jobs))

        # will implicitly cancel all jobs in the batch IN the API
        self.client.cancel_batch(self.id)

        # We do not touch the status here
        logger.info("Batch cancelled successfully.")

    def status(self) -> BatchJobStatus:
        """Return the status of the batch, among the values of ``BatchJobStatus``."""
        try:
            batch_status = self.client.get_batch_job(self.id).get("status")
            self._cache_metadata["status"] = BatchJobStatus(batch_status)
            return self._cache_metadata["status"]
        except Exception as e:
            logger.error("Failed to get status of batch '%s': %s", self.id, e)
            raise BatchJobError(f"Failed to get status of batch {self.id}.") from e

    @abstractmethod
    def aggregate(self) -> qbraid.runtime.BatchResult:
        """Aggregate the results of the batch into a single object. Depends on the provider
        and the type of the batch jobs."""

    def __repr__(self) -> str:
        """String representation of a BatchQuantumJob object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

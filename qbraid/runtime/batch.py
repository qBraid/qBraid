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

from qbraid._logging import logger

from .enums import BatchJobStatus, ExecutionMode
from .exceptions import BatchJobError
from .job import QuantumJob

if TYPE_CHECKING:
    import qbraid.runtime
    from qbraid.runtime.result_data import ResultDataType


class BatchQuantumJob(ABC):
    """Abstract interface for batch-like classes."""

    MAX_TIMEOUT_DEFAULT = 60 * 60  # 1 hour
    MAX_TIMEOUT_LIMIT = 24 * 60 * 60  # 24 hours

    def __init__(
        self, device: qbraid.runtime.QuantumDevice, max_timeout: Optional[int] = None, **kwargs
    ):
        self._device = device
        self._jobs: list[QuantumJob] = []
        self.max_timeout = max_timeout if max_timeout is not None else self.MAX_TIMEOUT_DEFAULT
        self._cache_metadata = {**kwargs}
        self._active = False
        self._batch_id = None

    @property
    def id(self) -> str | int:  # pylint: disable=invalid-name
        """Return a unique id identifying the batch."""
        return self._batch_id

    @property
    def device(self) -> qbraid.runtime.QuantumDevice:
        """Returns the qbraid QuantumDevice object associated with this batch."""
        return self._device

    @property
    def jobs(self) -> list[QuantumJob]:
        """Return the list of jobs in the batch."""
        return self._jobs

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
        try:
            # only after successfully creating the batch, we can set the batch id
            self._batch_id = self.device.create_batch(self.max_timeout, self._cache_metadata)
            self._active = True
        except Exception as e:
            logger.error(f"Failed to create batch on device {self.device.profile.device_id}: {e}")
            self._active = False
            raise BatchJobError(
                f"Failed to create batch on device {self.device.profile.device_id}."
            ) from e

    def close(self):
        """Close the batch job context."""
        if not self.is_active():
            logger.warning(f"Batch {self.id} is not active. No action taken on close.")
            return

        # closing the batch job context and updating execution mode
        # regardless of the success of the close operation
        self.active = False

        try:
            self.device.close_batch(self.id)
        except Exception as e:
            logger.error(
                f"Failed to close batch {self.id} on device {self.device.profile.device_id}: {e}"
            )
            raise BatchJobError(
                f"Failed to close batch {self.id} on device {self.device.profile.device_id}."
            ) from e

    def __enter__(self) -> BatchQuantumJob:
        """Enter the runtime context of the batch job."""
        self.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context of the batch job."""
        if exc_type is not None:
            logger.error(f"An error occurred while processing batch {self.id}: {exc_value}")

        self.close()
        return False

    def add_job(self, job: QuantumJob) -> None:
        """Add a job to the batch.

        Args:
            job: The QuantumJob to add to the batch.

        Raises:
            ValueError: If the job is already in the batch.
        """
        if job in self._jobs:
            raise ValueError(f"Job '{job.id}' is already in the batch '{self.id}'.")
        self._jobs.append(job)

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

    @abstractmethod
    def status(self) -> BatchJobStatus:
        """Return the status of the batch, among the values of ``BatchJobStatus``."""

    @abstractmethod
    def result(self) -> list[qbraid.runtime.Result[ResultDataType]]:
        """Return the results of the batch."""

    @abstractmethod
    def cancel(self) -> None:
        """Attempt to cancel the batch."""

    def __repr__(self) -> str:
        """String representation of a BatchQuantumJob object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

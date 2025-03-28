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
Module defining abstract QuantumJob Class

"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from time import sleep, time
from typing import TYPE_CHECKING, Any, Optional

from .enums import JobStatus
from .exceptions import ResourceNotFoundError

if TYPE_CHECKING:
    import qbraid.runtime
    from qbraid.runtime.result_data import ResultDataType


class QuantumJob(ABC):
    """Abstract interface for job-like classes."""

    def __init__(
        self, job_id: str | int, device: Optional[qbraid.runtime.QuantumDevice] = None, **kwargs
    ):
        self._job_id = job_id
        self._device = device
        self._cache_metadata = {"job_id": job_id, **kwargs}

    @property
    def id(self) -> str | int:  # pylint: disable=invalid-name
        """Return a unique id identifying the job."""
        return self._job_id

    @property
    def device(self) -> qbraid.runtime.QuantumDevice:
        """Returns the qbraid QuantumDevice object associated with this job."""
        if self._device is None:
            raise ResourceNotFoundError("Job does not have an associated device.")
        return self._device

    def is_terminal_state(self) -> bool:
        """Returns True if job is in final state. False otherwise."""
        terminal_states = JobStatus.terminal_states()
        if self._cache_metadata.get("status", None) in terminal_states:
            return True

        status = self.status()
        return status in terminal_states

    @abstractmethod
    def status(self) -> JobStatus:
        """Return the status of the job / task , among the values of ``JobStatus``."""

    def metadata(self) -> dict[str, Any]:
        """Return the metadata regarding the job."""
        status = self.status()
        self._cache_metadata["status"] = status
        return self._cache_metadata

    def wait_for_final_state(self, timeout: Optional[int] = None, poll_interval: int = 5) -> None:
        """Poll the job status until it progresses to a final state.

        Args:
            timeout: Seconds to wait for the job. If ``None``, wait indefinitely.
            poll_interval: Seconds between queries. Defaults to 5 seconds.

        Raises:
            JobStateError: If the job does not reach a final state before the specified timeout.

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
        """Asynchronously wait for the job to reach a terminal state (e.g., COMPLETED, FAILED).

        This non-blocking method uses asyncio to periodically poll the job's status,
        allowing other coroutines to run while waiting. It is especially useful in
        asynchronous applications where blocking the event loop is undesirable.

        Args:
            timeout (Optional[int]): Maximum number of seconds to wait for the job.
                If None, waits indefinitely.
            poll_interval (int): Seconds between queries. Defaults to 5.

        Raises:
            TimeoutError: If the job does not reach a terminal state before the specified timeout.
        """
        start_time = time()
        while not self.is_terminal_state():
            elapsed_time = time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise TimeoutError(f"Timeout while waiting for job {self.id}.")
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
    def result(self) -> qbraid.runtime.Result[ResultDataType]:
        """Return the results of the job."""

    @abstractmethod
    def cancel(self) -> None:
        """Attempt to cancel the job."""

    def __repr__(self) -> str:
        """String representation of a QuantumJob object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

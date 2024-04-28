# Copyright (C) 2023 qBraid
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
import logging
from abc import ABC, abstractmethod
from enum import Enum
from time import sleep, time
from typing import TYPE_CHECKING, Any, Optional, Union

from .device import Device
from .enums import JOB_FINAL, JobStatus
from .exceptions import JobError, ResourceNotFoundError
from .result import Result

if TYPE_CHECKING:
    import qbraid.providers

logger = logging.getLogger(__name__)


class Job:
    """Base common type for all Job classes."""


class QuantumJob(ABC, Job):
    """Abstract interface for job-like classes."""

    def __init__(self, job_id: str, device: Optional[Device], **kwargs):
        self._job_id = job_id
        self._device = device
        self._cache_metadata = kwargs
        self._cache_status = kwargs.get("status", None)

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Return a unique id identifying the job."""
        return self._job_id

    @property
    def device(self) -> Device:
        """Returns the qbraid QuantumDevice object associated with this job."""
        if self._device is None:
            raise ResourceNotFoundError("Job does not have an associated device.")
        return self._device

    @staticmethod
    def _map_status(status: Optional[Union[str, JobStatus]] = None) -> JobStatus:
        """Returns `JobStatus` object mapped from raw status value. If no value
        provided or conversion from string fails, returns `JobStatus.UNKNOWN`."""
        if status is None:
            return JobStatus.UNKNOWN
        if isinstance(status, Enum):
            return status
        if isinstance(status, str):
            for e in JobStatus:
                status_enum = JobStatus(e.value)
                if status == status_enum.name or status == str(status_enum):
                    return status_enum
            raise ValueError(f"Status value '{status}' not recognized.")
        raise ValueError(f"Invalid status value type: {type(status)}")

    @staticmethod
    def status_final(status: Union[str, JobStatus]) -> bool:
        """Returns True if job is in final state. False otherwise."""
        if isinstance(status, str):
            if status in JOB_FINAL:
                return True
            for job_status in JOB_FINAL:
                if job_status.name == status:
                    return True
            return False
        raise TypeError(
            f"Expected status of type 'str' or 'JobStatus' \
            but instead got status of type {type(status)}."
        )

    @abstractmethod
    def status(
        self,
    ) -> JobStatus:
        """Return the status of the job / task , among the values of ``JobStatus``."""

    def metadata(self) -> dict[str, Any]:
        """Return the metadata regarding the job."""
        status = self.status()
        if not self._cache_metadata or status != self._cache_status:
            self._cache_status = self._map_status(self._cache_metadata["status"])
        return self._cache_metadata

    def wait_for_final_state(self, timeout: Optional[int] = None, poll_interval: int = 5) -> None:
        """Poll the job status until it progresses to a final state.

        Args:
            timeout: Seconds to wait for the job. If ``None``, wait indefinitely.
            poll_interval: Seconds between queries. Defaults to 5 seconds.

        Raises:
            JobError: If the job does not reach a final state before the specified timeout.

        """
        start_time = time()
        status = self.status()
        while not self.status_final(status):
            elapsed_time = time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise JobError(f"Timeout while waiting for job {self.id}.")
            sleep(poll_interval)
            status = self.status()

    @abstractmethod
    def result(self) -> "qbraid.providers.ResultWrapper":
        """Return the results of the job."""

    @abstractmethod
    def cancel(self) -> None:
        """Attempt to cancel the job."""

    def __repr__(self) -> str:
        """String representation of a QuantumJob object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

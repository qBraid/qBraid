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
Module defining abstract JobLikeWrapper Class

"""
import logging
from abc import ABC, abstractmethod
from time import sleep, time
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from qbraid import device_wrapper
from qbraid.api import get_job_data

from .enums import JOB_FINAL, JobStatus, status_from_raw
from .exceptions import JobError
from .status_maps import STATUS_MAP

if TYPE_CHECKING:
    import qbraid


def _set_init_status(status: Optional[Union[str, JobStatus]]) -> JobStatus:
    """Returns `JobStatus` object with which to initialize job. If no value
    provided or conversion from string fails, returns `JobStatus.UNKNOWN`.
    """
    if isinstance(status, JobStatus):
        return status
    if isinstance(status, str):
        try:
            return status_from_raw(status)
        except ValueError:
            return JobStatus.UNKNOWN
    return JobStatus.UNKNOWN


class JobLikeWrapper(ABC):
    """Abstract interface for job-like classes."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        job_id: str,
        vendor_job_id: Optional[str] = None,
        device: "Optional[qbraid.providers.DeviceLikeWrapper]" = None,
        vendor_jlo: Optional[Any] = None,
        status: Optional[Union[str, JobStatus]] = None,
    ):
        self._cache_metadata = None
        self._cache_status = _set_init_status(status)
        self._job_id = job_id
        self._vendor_job_id = vendor_job_id
        self._device = device
        self._vendor_jlo = vendor_jlo
        self._status_map = STATUS_MAP[self.device.vendor]

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Return a unique id identifying the job."""
        return self._job_id

    @property
    def vendor_job_id(self) -> str:
        """Returns the ID assigned by the device vendor"""
        if self._vendor_job_id is None:
            self._cache_metadata = get_job_data(self.id)
            self._vendor_job_id = self._cache_metadata["vendorJobId"]
        return self._vendor_job_id

    @property
    def device(self) -> "qbraid.providers.DeviceLikeWrapper":
        """Returns the qbraid DeviceLikeWrapper object associated with this job."""
        if self._device is None:
            self._device = device_wrapper(self.id.split(":")[0])
        return self._device

    @property
    def vendor_jlo(self) -> Any:
        """Return the job like object that is being wrapped."""
        if self._vendor_jlo is None:
            self._vendor_jlo = self._get_vendor_jlo()
        return self._vendor_jlo

    @abstractmethod
    def _get_vendor_jlo(self):
        """Return the job like object that is being wrapped."""

    def _status(self) -> Tuple[JobStatus, str]:
        vendor_status = self._get_status()
        try:
            return self._status_map[vendor_status], vendor_status
        except KeyError:
            logging.warning(
                "Expected %s job status matching one of %s but instead got '%s'.",
                self._device.vendor,
                str(list(self._status_map.keys())),
                vendor_status,
            )
            return JobStatus.UNKNOWN, vendor_status

    def status(self) -> JobStatus:
        """Return the status of the job / task , among the values of ``JobStatus``."""
        qbraid_status, vendor_status = self._status()
        if qbraid_status != self._cache_status:
            update = {"status": vendor_status, "qbraidStatus": qbraid_status.raw()}
            _ = get_job_data(self.id, update=update)
        return qbraid_status

    @abstractmethod
    def _get_status(self) -> str:
        """Status method helper function. Uses ``vendor_jlo`` to get status of the job / task, casts
        as string if necessary, returns result."""

    def metadata(self) -> Dict[str, Any]:
        """Return the metadata regarding the job."""
        qbraid_status, vendor_status = self._status()
        if not self._cache_metadata or qbraid_status != self._cache_status:
            update = {"status": vendor_status, "qbraidStatus": qbraid_status.raw()}
            self._cache_metadata = get_job_data(self.id, update=update)
            self._cache_status = status_from_raw(self._cache_metadata["qbraidStatus"])
        return self._cache_metadata

    def wait_for_final_state(self, timeout=None, wait=5) -> None:
        """Poll the job status until it progresses to a final state.

        Args:
            timeout: Seconds to wait for the job. If ``None``, wait indefinitely.
            wait: Seconds between queries.

        Raises:
            JobError: If the job does not reach a final state before the specified timeout.

        """
        start_time = time()
        status = self.status()
        while status not in JOB_FINAL:
            elapsed_time = time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise JobError(f"Timeout while waiting for job {self.id}.")
            sleep(wait)
            status = self.status()

    @abstractmethod
    def result(self) -> "qbraid.providers.ResultWrapper":
        """Return the results of the job."""

    @abstractmethod
    def cancel(self) -> None:
        """Attempt to cancel the job."""

    def __repr__(self) -> str:
        """String representation of a JobLikeWrapper object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

"""JobLikeWrapper Class"""

import logging
from abc import ABC, abstractmethod
from time import sleep, time
from typing import Any, Dict

import qbraid
from qbraid.api import job_api
from qbraid.api.status_maps import STATUS_MAP
from qbraid.devices.enums import JOB_FINAL, JobStatus
from qbraid.devices.exceptions import JobError


class JobLikeWrapper(ABC):
    """Abstract interface for job-like classes."""

    def __init__(self, job_id, vendor_job_id, device, vendor_jlo):
        self._cache_metadata = None
        self._cache_status = None
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
    def vendor_job_id(self):
        """Returns the ID assigned by the device vendor"""
        if self._vendor_job_id is None:
            self._cache_metadata = job_api.mongo_get_job(self.id)
            self._cache_status = self._cache_metadata["status"]
            self._vendor_job_id = self._cache_metadata["vendorJobId"]
        return self._vendor_job_id

    @property
    def device(self):
        """Returns the qbraid DeviceLikeWrapper object associated with this job."""
        if self._device is None:
            self._device = qbraid.device_wrapper(self.id.split(":")[0])
        return self._device

    @property
    def vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        if self._vendor_jlo is None:
            self._vendor_jlo = self._get_vendor_jlo()
        return self._vendor_jlo

    @abstractmethod
    def _get_vendor_jlo(self):
        """Return the job like object that is being wrapped."""

    def status(self) -> JobStatus:
        """Return the status of the job / task , among the values of ``JobStatus``."""
        vendor_status = self._get_status()
        try:
            return self._status_map[vendor_status]
        except KeyError:
            logging.warning(
                "Expected %s job status matching one of %s but instead got '%s'.",
                self._device.vendor,
                str(list(self._status_map.keys())),
                vendor_status,
            )
            return JobStatus.UNKNOWN

    @abstractmethod
    def _get_status(self) -> str:
        """Status method helper function. Uses vendor_jlo to get status of the job / task, casts
        as string if necessary, returns result."""

    def metadata(self) -> Dict[str, Any]:
        """Return the metadata regarding the job."""
        status = self.status()
        if not self._cache_metadata or status != self._cache_status:
            self._cache_status = status
            self._cache_metadata = job_api.mongo_get_job(self.id, update={"status": status.name})
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
    def result(self):
        """Return the results of the job."""

    @abstractmethod
    def cancel(self):
        """Attempt to cancel the job."""

    def __repr__(self) -> str:
        """String representation of a JobLikeWrapper object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

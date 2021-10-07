"""JobLikeWrapper Class"""

from abc import ABC, abstractmethod
import logging
from time import time, sleep
from typing import Any, Dict

import qbraid
from qbraid.devices import JobError
from qbraid.devices.enums import Status, STATUS_FINAL
from ._utils import mongo_get_job, STATUS_MAP


class JobLikeWrapper(ABC):
    """Abstract interface for job-like classes.

    """

    def __init__(self, job_id, vendor_job_id, device, vendor_jlo):
        self._cache_metadata = None
        self._cache_status = None
        self._job_id = job_id
        self._vendor_job_id = vendor_job_id
        self._device = qbraid.device_wrapper(job_id.split(":")[0]) if not device else device
        self._vendor_jlo = self.vendor_jlo if not vendor_jlo else vendor_jlo
        self._status_map = STATUS_MAP[self._device.vendor]

    @property
    def id(self) -> str:
        """Return a unique id identifying the job."""
        return self._job_id

    @property
    def vendor_job_id(self):
        if not self._vendor_job_id:
            self._cache_metadata = mongo_get_job(self.id)
            self._cache_status = self._cache_metadata["status"]
            self._vendor_job_id = self._cache_metadata["vendor_job_id"]
        return self._vendor_job_id

    @property
    @abstractmethod
    def vendor_jlo(self):
        """Return the job like object that is being wrapped."""

    def status(self) -> Status:
        """Return the status of the job / task , among the values of ``Status``."""
        vendor_status = self._status()
        try:
            return self._status_map[vendor_status]
        except KeyError:
            logging.warning(
                f"Expected {self._device.vendor} job status matching one of "
                f"{list(self._status_map.keys())}, but instead got '{vendor_status}'."
            )
            return Status.UNKNOWN

    @abstractmethod
    def _status(self) -> str:
        """Status method helper function. Uses vendor_jlo to get status of the job / task, casts
        as string if necessary, returns result. """

    def metadata(self) -> Dict[str, Any]:
        """Return the metadata regarding the job."""
        status = self.status()
        if not self._cache_metadata or status != self._cache_status:
            self._cache_status = status
            self._cache_metadata = mongo_get_job(self.id, update={"status": status.name})
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
        while status not in STATUS_FINAL:
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

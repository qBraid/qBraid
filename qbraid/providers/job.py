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
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from qbraid.api import QbraidSession

from .enums import JOB_FINAL, JobStatus
from .exceptions import JobError
from .status_maps import STATUS_MAP

if TYPE_CHECKING:
    import qbraid


class QuantumJob(ABC):
    """Abstract interface for job-like classes."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        job_id: str,
        vendor_job_id: Optional[str] = None,
        device: "Optional[qbraid.providers.QuantumDevice]" = None,
        vendor_job_obj: Optional[Any] = None,
        status: Optional[Union[str, JobStatus]] = None,
    ):
        self._cache_metadata = None
        self._cache_status = self._map_status(status)
        self._job_id = job_id
        self._vendor_job_id = vendor_job_id
        self._device = device
        self._job = vendor_job_obj or self._get_job()
        self._status_map = STATUS_MAP[self.device.vendor]

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Return a unique id identifying the job."""
        return self._job_id

    @property
    def vendor_job_id(self) -> str:
        """Returns the ID assigned by the device vendor"""
        if self._vendor_job_id is None:
            self._cache_metadata = self._post_job_data()
            self._vendor_job_id = self._cache_metadata["vendorJobId"]
        return self._vendor_job_id

    @property
    def device(self) -> "qbraid.providers.QuantumDevice":
        """Returns the qbraid QuantumDevice object associated with this job."""
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
            update = {"status": vendor_status, "qbraidStatus": qbraid_status.name}
            _ = self._post_job_data(update=update)
        return qbraid_status

    def _post_job_data(self, update: Optional[dict] = None) -> dict:
        """Retreives job metadata and optionally updates document.

        Args:
            update: Dictionary containing fields to update in job document.

        Returns:
            The metadata associated with this job

        """
        session = QbraidSession()
        body = {"qbraidJobId": self.id}
        # Two status variables so we can track both qBraid and vendor status.
        if update is not None and "status" in update and "qbraidStatus" in update:
            body["status"] = update["status"]
            body["qbraidStatus"] = update["qbraidStatus"]
        metadata = session.put("/update-job", data=body).json()[0]
        metadata.pop("_id", None)
        metadata.pop("user", None)
        return metadata

    def metadata(self) -> Dict[str, Any]:
        """Return the metadata regarding the job."""
        qbraid_status, vendor_status = self._status()
        if not self._cache_metadata or qbraid_status != self._cache_status:
            update = {"status": vendor_status, "qbraidStatus": qbraid_status.name}
            self._cache_metadata = self._post_job_data(update=update)
            self._cache_status = self._map_status(self._cache_metadata["qbraidStatus"])
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
        while not self.status_final(status):
            elapsed_time = time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise JobError(f"Timeout while waiting for job {self.id}.")
            sleep(wait)
            status = self.status()

    @abstractmethod
    def _get_job(self):
        """Return the job like object that is being wrapped."""

    @abstractmethod
    def _get_status(self) -> str:
        """Returns job status casted as string."""

    @abstractmethod
    def result(self) -> "qbraid.providers.ResultWrapper":
        """Return the results of the job."""

    @abstractmethod
    def cancel(self) -> None:
        """Attempt to cancel the job."""

    def __repr__(self) -> str:
        """String representation of a QuantumJob object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

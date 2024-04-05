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
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from qbraid_core.services.quantum import QuantumClient, QuantumServiceRequestError

from qbraid._import import _load_entrypoint

from .enums import JOB_FINAL, JobStatus
from .exceptions import JobError, ResourceNotFoundError
from .provider import QbraidProvider
from .status_maps import STATUS_MAP

if TYPE_CHECKING:
    import qbraid

logger = logging.getLogger(__name__)


class QuantumJob(ABC):
    """Abstract interface for job-like classes."""

    @classmethod
    def retrieve(cls, job_id: str, **kwargs) -> "qbraid.providers.QuantumJob":
        """Create a QuantumJob object from a job_id."""
        try:
            vendor = job_id.split("_")[0]
            job_class = _load_entrypoint("providers", f"{vendor}.job")
        except (ValueError, IndexError) as err:
            raise ResourceNotFoundError(f"Invalid Job Id {job_id}.") from err
        return job_class(job_id, **kwargs)

    def __init__(  # pylint: disable=too-many-arguments
        self,
        job_id: str,
        job_obj: Optional[Any] = None,
        job_json: Optional[Dict[str, Any]] = None,
        device: "Optional[qbraid.providers.QuantumDevice]" = None,
        circuits: "Optional[List[qbraid.programs.QuantumProgram]]" = None,
        provider: Optional[QbraidProvider] = None,
    ):
        if type(self) is QuantumJob:  # pylint: disable=unidiomatic-typecheck
            raise NotImplementedError(
                "QuantumJob is an abstract class and cannot be instantiated directly."
            )
        self._job_id = job_id
        self._provider = provider
        self._client = None

        job_data = job_json or self._fetch_metadata()
        self._cache_metadata = job_data
        self._cache_status = job_data.get("qbraidStatus", job_data.get("status"))
        self._vendor = job_data.get("vendor")
        self._vendor_job_id = job_data.get("vendorJobId")
        self._device = device or self.provider.get_device(job_data["qbraidDeviceId"])
        self._job = job_obj or self._get_job()
        self._status_map = STATUS_MAP[self.vendor]
        self._circuits = circuits

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Return a unique id identifying the job."""
        return self._job_id

    @property
    def provider(self) -> QbraidProvider:
        """Return the quantum client object."""
        if self._provider is None:
            self._provider = QbraidProvider()
        return self._provider

    @property
    def client(self) -> QuantumClient:
        """Return the quantum client object."""
        if self._client is None:
            self._client = self.provider.client
        return self._client

    @property
    def vendor(self) -> str:
        """Get job vendor."""
        if self._vendor is not None:
            return self._vendor.upper()

        try:
            vendor = self._cache_metadata["vendor"]
        except (KeyError, TypeError):
            vendor = self.device.vendor

        self._vendor = vendor.upper()
        return self._vendor

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
        if self._device is None:
            qbraid_device_id = self._cache_metadata["qbraidDeviceId"]
            self._device = self.client.get_device(qbraid_device_id)
        return self._device

    def _fetch_metadata(self) -> Dict[str, Any]:
        first_error = None

        # Attempt to get the device data first with the qbraid_id and then with the vendor_id
        get_job_functions = [
            lambda: self.client.get_job(qbraid_id=self.id),
            lambda: self.client.get_job(object_id=self.id),
        ]

        for get_job_function in get_job_functions:
            try:
                return get_job_function()
            except (ValueError, QuantumServiceRequestError) as err:
                first_error = first_error or err

        raise ResourceNotFoundError(f"Quantum Job {self.id} not found.") from first_error

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
            logger.warning(
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
            self._post_job_data(
                update={"status": vendor_status, "qbraidStatus": qbraid_status.name}
            )
        return qbraid_status

    def _post_job_data(self, update: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retreives job metadata and optionally updates document.

        Args:
            update: Dictionary containing fields to update in job document.

        Returns:
            The metadata associated with this job

        """
        if self._device and self._device._device_type.name == "FAKE":
            return self._cache_metadata

        client = QuantumClient()
        body = {"_id": self.id} if client._is_valid_object_id(self.id) else {"qbraidJobId": self.id}
        # Two status variables so we can track both qBraid and vendor status.
        if update is not None and "status" in update and "qbraidStatus" in update:
            body["status"] = update["status"]
            body["qbraidStatus"] = update["qbraidStatus"]
        metadata = client.update_job(data=body)
        if "qbraidJobId" not in metadata:
            metadata["qbraidJobId"] = metadata.get("_id")
        return metadata

    def metadata(self) -> Dict[str, Any]:
        """Return the metadata regarding the job."""
        qbraid_status, vendor_status = self._status()
        if not self._cache_metadata or qbraid_status != self._cache_status:
            update = {"status": vendor_status, "qbraidStatus": qbraid_status.name}
            self._cache_metadata = self._post_job_data(update=update)
            self._cache_status = self._map_status(self._cache_metadata["qbraidStatus"])
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

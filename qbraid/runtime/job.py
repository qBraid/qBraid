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
from time import sleep, time
from typing import TYPE_CHECKING, Any, Optional

from qbraid_core.services.quantum import QuantumClient

from .enums import JOB_STATUS_FINAL, JobStatus
from .exceptions import JobError, JobStateError, ResourceNotFoundError
from .result import ExperimentResult, QbraidJobResult

if TYPE_CHECKING:
    import qbraid_core.services.quantum

    import qbraid.runtime

logger = logging.getLogger(__name__)


class QuantumJob(ABC):
    """Abstract interface for job-like classes."""

    def __init__(
        self, job_id: str, device: "Optional[qbraid.runtime.QuantumDevice]" = None, **kwargs
    ):
        self._job_id = job_id
        self._device = device
        self._cache_metadata = {"job_id": job_id, **kwargs}

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Return a unique id identifying the job."""
        return self._job_id

    @property
    def device(self) -> "qbraid.runtime.QuantumDevice":
        """Returns the qbraid QuantumDevice object associated with this job."""
        if self._device is None:
            raise ResourceNotFoundError("Job does not have an associated device.")
        return self._device

    def is_terminal_state(self) -> bool:
        """Returns True if job is in final state. False otherwise."""
        if self._cache_metadata.get("status", None) in JOB_STATUS_FINAL:
            return True

        status = self.status()
        return status in JOB_STATUS_FINAL

    @abstractmethod
    def status(self) -> JobStatus:
        """Return the status of the job / task , among the values of ``JobStatus``."""

    def metadata(self, use_cache: bool = False) -> dict[str, Any]:
        """Return the metadata regarding the job."""
        if not use_cache:
            status = self.status()
            self._cache_metadata["status"] = status
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
        while not self.is_terminal_state():
            elapsed_time = time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise JobError(f"Timeout while waiting for job {self.id}.")
            sleep(poll_interval)

    @abstractmethod
    def result(self) -> "qbraid.runtime.QuantumJobResult":
        """Return the results of the job."""

    @abstractmethod
    def cancel(self) -> None:
        """Attempt to cancel the job."""

    def __repr__(self) -> str:
        """String representation of a QuantumJob object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"


class QbraidJob(QuantumJob):
    """Class representing a qBraid job."""

    def __init__(
        self,
        job_id: str,
        device: "Optional[qbraid.runtime.QbraidDevice]" = None,
        client: "Optional[qbraid_core.services.quantum.QuantumClient]" = None,
        **kwargs,
    ):
        super().__init__(job_id, device, **kwargs)
        self._client = client

    @property
    def client(self) -> "qbraid_core.services.quantum.QuantumClient":
        """
        Lazily initializes and returns the client object associated with the job.
        If the job has an associated device with a client, that client is used.
        Otherwise, a new instance of QuantumClient is created and used.

        Returns:
            QuantumClient: The client object associated with the job.
        """
        if self._client is None:
            self._client = self._device.client if self._device else QuantumClient()
        return self._client

    @staticmethod
    def _map_status(status: Optional[str]) -> JobStatus:
        """Returns `JobStatus` object mapped from raw status value. If no value
        provided or conversion from string fails, returns `JobStatus.UNKNOWN`."""
        if status is None:
            return JobStatus.UNKNOWN
        if not isinstance(status, str):
            raise ValueError(f"Invalid status value type: {type(status)}")
        for e in JobStatus:
            status_enum = JobStatus(e.value)
            if status == status_enum.name or status == str(status_enum):
                return status_enum
        raise ValueError(f"Status value '{status}' not recognized.")

    def status(self) -> JobStatus:
        """Return the status of the job / task , among the values of ``JobStatus``."""
        job_data = self.client.get_job(self.id)
        status = job_data.get("status")
        return self._map_status(status)

    def cancel(self) -> None:
        """Attempt to cancel the job."""
        if self.is_terminal_state():
            raise JobStateError("Cannot cancel job in a terminal state.")

        self.client.cancel_job(self.id)

    def result(self) -> "qbraid.runtime.QuantumJobResult":
        """Return the results of the job."""
        self.wait_for_final_state()
        job_data = self.client.get_job(self.id)
        result = job_data.get("result")
        if not result:
            raise ResourceNotFoundError("Job result not found.")

        device_id: str = result.get("qbraidDeviceId")
        success: bool = result.get("status") == "COMPLETED"
        result = ExperimentResult.from_result(result)
        return QbraidJobResult(device_id, self.id, success, result)

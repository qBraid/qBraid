"""JobLikeWrapper Class"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Dict
from time import time, sleep

from qbraid.devices.enums import Status, STATUS_FINAL
from qbraid.devices import JobError
from ._utils import mongo_init_job, mongo_update_job, STATUS_MAP


class JobLikeWrapper(ABC):
    """Abstract interface for job-like classes.

    Args:
        device: qbraid wrapped device object used in this job
        circuit: qbraid wrapped circuit object used in this job
        vendor_jlo: job-like object used to run circuits

    """

    def __init__(self, device, circuit, vendor_jlo):
        self.device = device
        self.circuit = circuit
        self._vendor_jlo = vendor_jlo
        self._status_map = STATUS_MAP[self.device.vendor]
        self._cache_status = None
        self._cache_metadata = None
        self._init_data = {
            "qbraid_job_id": None,
            "vendor_job_id": self.vendor_job_id,
            "qbraid_device_id": self.device.id,
            "circuit_num_qubits": self.circuit.num_qubits,
            "circuit_depth": self.circuit.depth,
            "shots": self._shots,
            "createdAt": datetime.now(),
            "status": Status.INITIALIZING,
        }
        self._qbraid_job_id = mongo_init_job(self._init_data)

    @property
    def vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        return self._vendor_jlo

    @property
    def id(self) -> str:
        """Return a unique id identifying the job."""
        return self._qbraid_job_id

    @property
    @abstractmethod
    def vendor_job_id(self) -> str:
        """Return the job ID from the vendor job-like-object."""

    @property
    @abstractmethod
    def _shots(self) -> int:
        """Return the number of repetitions used in the run"""

    def status(self) -> Status:
        """Return the status of the job / task , among the values of ``Status``."""
        vendor_status = self._status()
        try:
            return self._status_map[vendor_status]
        except KeyError:
            logging.warning(
                f"Expected {self.device.vendor} job status matching one of "
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
            self._cache_metadata = mongo_update_job(self.id, {"status": status.name})
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

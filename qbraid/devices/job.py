"""JobLikeWrapper Class"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ._utils import mongo_init_job, mongo_update_job


class JobLikeWrapper(ABC):
    """Abstract interface for job-like classes.

    Args:
        qbraid_device: qbraid wrapped device object used in this job
        qbraid_circuit: qbraid wrapped circuit object used in this job
        vendor_jlo: job-like object used to run circuits

    """

    def __init__(self, qbraid_device, qbraid_circuit, vendor_jlo):
        self._init_data = {
            "qbraid_job_id": None,
            "qbraid_device_id": qbraid_device.id,
            "device_name": f"{qbraid_device.provider} {qbraid_device.name}",
            "circuit_num_qubits": qbraid_circuit.num_qubits,
            "circuit_depth": qbraid_circuit.depth,
        }
        self._vendor_jlo = vendor_jlo
        self._init_data.update(self._set_static())
        self._qbraid_job_id = mongo_init_job(self._init_data)
        self._metadata_old = None

    @property
    def vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        return self._vendor_jlo

    @property
    def id(self) -> str:
        """Return a unique id identifying the job."""
        return self._qbraid_job_id

    @abstractmethod
    def _set_static(self):
        """Return a dictionary that provides key-value mappings for the following keys:
        * vendor_job_id (str): the job ID from the vendor job-like-object.
        * createdAt (datetime.datime): the time the job was created
        * shots (int): the number of repetitions used in the run

        """

    @abstractmethod
    def status(self):
        """State of the quantum task.

        Returns:
            str: CREATED | QUEUED | RUNNING | COMPLETED | FAILED | CANCELLING | CANCELLED

        """

    @abstractmethod
    def ended_at(self):
        """The time when the job ended."""

    def metadata(self, **kwargs) -> Dict[str, Any]:
        """Return the metadata regarding the job."""
        status = self.status()
        if self._metadata_old and status == self._metadata_old["status"]:
            return self._metadata_old
        data = {"status": status}
        if status in ["COMPLETED", "FAILED", "CANCELED"]:
            data["endedAt"] = self.ended_at()
        return mongo_update_job(self.id, data)

    @abstractmethod
    def result(self):
        """Return the results of the job."""

    @abstractmethod
    def cancel(self):
        """Attempt to cancel the job."""

    def __repr__(self) -> str:
        """String representation of a JobLikeWrapper object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

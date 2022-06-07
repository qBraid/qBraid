"""JobLikeWrapper Class"""

# pylint: disable=invalid-name

from abc import ABC, abstractmethod
from typing import Any, Dict

from .enums import JobStatus
from .exceptions import JobError


class LocalJobWrapper(ABC):
    """Abstract interface for job-like classes.

    Args:
        device: qBraid device wrapper object
        vendor_jlo: A job-like object used to run circuits.
    """

    def __init__(self, device, vendor_jlo):

        self.device = device
        self.vendor_jlo = vendor_jlo

    @property
    @abstractmethod
    def id(self) -> str:
        """Return a unique id identifying the job."""

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return the metadata regarding the job."""

    @abstractmethod
    def result(self):
        """Return the results of the job."""

    def status(self):
        """Return the status of the job."""
        return JobStatus.COMPLETED

    def cancel(self) -> None:
        """Cancel current job"""
        raise JobError("Cannot cancel a completed job.")

    def __repr__(self) -> str:
        """String representation of a LocalJobLikeWrapper object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

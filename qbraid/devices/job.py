# This code is part of Qiskit.
#
# (C) Copyright IBM 2017.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of the source tree https://github.com/Qiskit/qiskit-terra/blob/main/LICENSE.txt
# or at http://www.apache.org/licenses/LICENSE-2.0.
#
# NOTICE: This file has been modified from the original:
# https://github.com/Qiskit/qiskit-terra/blob/main/qiskit/providers/job.py

"""JobLikeWrapper Class"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class JobLikeWrapper(ABC):
    """Abstract interface for job-like classes.

    Args:
        device: qbraid device wrapper object
        vendor_jlo: a job-like object used to run circuits.

    """

    def __init__(self, device, vendor_jlo):

        self.device = device
        self.vendor_jlo = vendor_jlo

    @property
    @abstractmethod
    def job_id(self) -> str:
        """Return a unique id identifying the job."""

    @abstractmethod
    def metadata(self, **kwargs) -> Dict[str, Any]:
        """Return the metadata regarding the job."""

    @abstractmethod
    def result(self):
        """Return the results of the job."""

    @abstractmethod
    def status(self):
        """Return the status of the job."""

    def cancel(self) -> None:
        """Attempt to cancel the job."""
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation of a JobLikeWrapper object."""
        return f"<{self.__class__.__name__}(id:'{self.job_id}')>"

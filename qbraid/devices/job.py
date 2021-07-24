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

from abc import ABC, abstractmethod
from typing import Dict, Any


class JobLikeWrapper(ABC):
    def __init__(self, device, vendor_jlo):
        """Abstract interface for job-like classes.
        Args:
            vendor_jlo: a job-like object used to run circuits.
            device: qbraid device wrapper object
        """
        self.device = device
        self.vendor_jlo = vendor_jlo  # vendor job-like object

    @property
    @abstractmethod
    def id(self) -> str:
        """Return a unique id identifying the job."""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return the metadata regarding the job."""
        pass

    @abstractmethod
    def result(self):
        """Return the results of the job."""
        pass

    @abstractmethod
    def status(self):
        """Return the status of the job."""
        pass

    def cancel(self) -> None:
        """Attempt to cancel the job."""
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation of a JobLikeWrapper object."""
        return f"<{self.__class__.__name__}(id:'{self.id}')>"

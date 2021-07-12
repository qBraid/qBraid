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

from abc import abstractmethod
from .device import DeviceLikeWrapper
from .wrapper import QbraidJobLikeWrapper
from typing import Dict, Any


class JobLikeWrapper(QbraidJobLikeWrapper):
    def __init__(self, vendor_jlo):
        """Abstract interface for job-like classes.
        Args:
            vendor_jlo: a job-like object used to run circuits.
        """
        self.vendor_jlo = vendor_jlo  # vendor job-like object
        self._device = None  # to be set after instantiation

    @property
    def device(self) -> DeviceLikeWrapper:
        """Return the :class:`~qbraid.devices.device.DeviceWrapper` where this job was executed."""
        if self._device is None:
            raise SystemError("device property of JobWrapper object is None")
        return self._device

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

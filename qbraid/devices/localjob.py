# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=invalid-name

"""
Module defining abstract LocalJobWrapper Class

"""

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

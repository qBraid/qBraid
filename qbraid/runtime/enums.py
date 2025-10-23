# Copyright 2025 qBraid
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

"""
Module defining all :mod:`~qbraid.runtime` enumerated types.

"""
from __future__ import annotations

from enum import Enum, IntEnum


class DeviceStatus(Enum):
    """Enumeration for representing various operational statuses of devices.

    Attributes:
        ONLINE (str): Device is online and accepting jobs.
        UNAVAILABLE (str): Device is online but not accepting jobs.
        OFFLINE (str): Device is offline.
        RETIRED (str): Device has been retired and is no longer operational.
    """

    ONLINE = "online"
    UNAVAILABLE = "unavailable"
    OFFLINE = "offline"
    RETIRED = "retired"


class JobStatus(Enum):
    """Enum for the status of processes (i.e. quantum jobs / tasks) resulting
    from any :meth:`~qbraid.runtime.QuantumDevice.run` method.

    Displayed status text values may differ from those listed below to provide
    additional visibility into tracebacks, particularly for failed jobs.

    """

    def __new__(cls, value: str):
        """Enumeration representing the status of a :py:class:`QuantumJob`."""
        obj = object.__new__(cls)
        obj._value_ = value
        obj.default_message = cls._get_default_message(value)
        obj.status_message = None
        return obj

    @classmethod
    def _get_default_message(cls, status: str) -> str:
        """Get the default message for a given status value."""
        default_messages = {
            "INITIALIZING": "job is being initialized",
            "QUEUED": "job is queued",
            "VALIDATING": "job is being validated",
            "RUNNING": "job is actively running",
            "CANCELLING": "job is being cancelled",
            "CANCELLED": "job has been cancelled",
            "COMPLETED": "job has successfully run",
            "FAILED": "job failed / incurred error",
            "UNKNOWN": "job status is unknown/undetermined",
            "HOLD": "job terminal but results withheld due to account status",
        }
        message = default_messages.get(status)

        if message is None:
            raise ValueError(f"Invalid status value: {status}")

        return message

    def set_status_message(self, message: str) -> None:
        """Set a custom message for the enum instance."""
        self.status_message = message

    def __repr__(self):
        """Custom repr to show custom message or default."""
        message = self.status_message if self.status_message else self.default_message
        return f"<{self.name}: '{message}'>"

    def __call__(self) -> JobStatus:
        """Create a new instance of the enum member, allowing unique attributes."""
        obj = self.__class__(self._value_)
        obj.default_message = self.default_message
        return obj

    @classmethod
    def terminal_states(cls) -> set[JobStatus]:
        """Returns the final job statuses."""
        return {cls.COMPLETED, cls.CANCELLED, cls.FAILED}

    INITIALIZING = "INITIALIZING"
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    HOLD = "HOLD"


class ValidationLevel(IntEnum):
    """Enumeration for program validation levels in qBraid runtime.

    Attributes:
        NONE (int): No validation is performed.
        WARN (int): Validation is performed, and warnings are issued if validation fails.
        RAISE (int): Validation is performed, and exceptions are raised if validation fails.
    """

    NONE = 0
    WARN = 1
    RAISE = 2

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

"""
Module defining all :mod:`~qbraid.devices` enumerated types.

"""
from enum import Enum
from typing import Union


class DeviceType(str, Enum):
    """Class for possible device types.

    Attributes:
        SIMULATOR (str): the device is a simulator
        QPU (str): the device is a QPU

    """

    SIMULATOR = "SIMULATOR"
    QPU = "QPU"


class DeviceStatus(int, Enum):
    """Class for the status of devices.

    Attributes:
        ONLINE (int): the device is online
        OFFLINE (int): the device is offline

    """

    ONLINE = 0
    OFFLINE = 1


class JobStatus(str, Enum):
    """Class for the status of processes (i.e. jobs / quantum tasks) resulting from any
    :meth:`~qbraid.devices.DeviceLikeWrapper.run` method.

    Attributes:
        INITIALIZING (str): job is being initialized
        QUEUED (str): job is queued
        VALIDATING (str): job is being validated
        RUNNING (str): job is actively running
        CANCELLING (str): job is being cancelled
        CANCELLED (str): job has been cancelled
        COMPLETED (str): job has successfully run
        FAILED (str): job failed / incurred error
        UNKNOWN (str): vendor-supplied job status not recognized

    """

    INITIALIZING = "job is being initialized"
    QUEUED = "job is queued"
    VALIDATING = "job is being validated"
    RUNNING = "job is actively running"
    CANCELLING = "job is being cancelled"
    CANCELLED = "job has been cancelled"
    COMPLETED = "job has successfully run"
    FAILED = "job failed / incurred error"
    UNKNOWN = "vendor-supplied job status not recognized"

    def raw(self):
        """Returns raw status string"""
        return str(self)[10:]


JOB_FINAL = (JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.FAILED)


def status_from_raw(status_str: str) -> JobStatus:
    """Returns JobStatus representation of input raw status string."""
    for e in JobStatus:
        status_enum = JobStatus(e.value)
        if status_str == status_enum.raw() or status_str == str(status_enum):
            return status_enum
    raise ValueError(f"Raw status '{status_str}' not recognized.")


def is_status_final(status: Union[str, JobStatus]) -> bool:
    """Returns True if job is in final state. False otherwise."""
    if isinstance(status, str):
        if status in JOB_FINAL:
            return True
        for job_status in JOB_FINAL:
            if job_status.raw() == status:
                return True
        return False
    raise TypeError(
        f"Expected status of type 'str' or 'JobStatus' \
        but instead got status of type {type(status)}."
    )

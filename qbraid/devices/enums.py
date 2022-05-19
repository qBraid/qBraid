"""This module defines all :mod:`~qbraid.devices` enumerated types."""
import enum
from typing import Union


class DeviceType(enum.IntEnum):
    """Class for the types of devies.

    Attributes:
        LOCALSIM (int): local simulator
        REMOTESIM (int): remote simulator
        QPUGATE (int): gate-baed qpu
        QPUANN (int): quantum annealer

    """

    LOCALSIM = 0
    REMOTESIM = 2
    QPUGATE = 1
    QPUANN = 3


class DeviceStatus(enum.IntEnum):
    """Class for the status of devies.

    Attributes:
        ONLINE (int): the device is online
        OFFLINE (int): the device is offline

    """

    ONLINE = 0
    OFFLINE = 1


class JobStatus(enum.IntEnum):
    """Class for the status of processes (i.e. jobs / quantum tasks) resulting from any
    :meth:`~qbraid.devices.DeviceLikeWrapper.run` method.

    Attributes:
        INITIALIZING (int): job is being initialized
        QUEUED (int): job is queued
        VALIDATING (int): job is being validated
        RUNNING (int): job is actively running
        CANCELLING (int): job is being cancelled
        CANCELLED (int): job has been cancelled
        COMPLETED (int): job has successfully run
        FAILED (int): job failed / incurred error
        UNKNOWN (int): vendor-supplied job status not recognized

    """

    INITIALIZING = 0
    QUEUED = 1
    VALIDATING = 2
    RUNNING = 3
    CANCELLING = 4
    CANCELLED = 5
    COMPLETED = 6
    FAILED = 7
    UNKNOWN = 8

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
        for job_status in JOB_FINAL:
            if job_status.raw() == status:
                return True
    elif isinstance(status, JobStatus):
        for job_status in JOB_FINAL:
            if job_status == status:
                return True
    else:
        raise TypeError(
            f"Expected status of type 'str' or 'JobStatus' \
            but instead got status of type {type(status)}."
        )
    return False

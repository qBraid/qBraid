"""This module defines all :mod:`~qbraid.devices` enumerated types."""

import enum


class DeviceType(enum.IntEnum):
    LOCALSIM = 0
    REMOTESIM = 2
    QPUGATE = 1
    QPUANN = 3


class DeviceStatus(enum.IntEnum):
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


JOB_FINAL = (JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.FAILED)
